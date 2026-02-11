import click
import typer
from pathlib import Path
import platform

from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from gmail_cleanup.gmail import (
    get_gmail_service,
    credentials_path,
    token_path,
    _app_data_dir,
    SCOPES,
)
from gmail_cleanup.preview import count_messages, sample_messages
from gmail_cleanup.labels import get_or_create_label_id, apply_label_to_messages
from gmail_cleanup.exporter import fetch_message_row, write_csv, write_json
from gmail_cleanup.trash import trash_message_ids
from gmail_cleanup.label_clear import remove_label
from gmail_cleanup.stats import collect_sender_counts_and_dates
from gmail_cleanup.config import load_config, config_path, write_template
from gmail_cleanup.gmail_iter import iter_message_id_pages
from gmail_cleanup.query_builder import QueryOptions, build_query

CFG = load_config()
console = Console()
app = typer.Typer(add_completion=False, invoke_without_command=True)


# ──────────────────────────────────────────────────────────────
# APP ENTRY
# ──────────────────────────────────────────────────────────────

@app.callback()
def main(
    ctx: click.Context,
    version: bool = typer.Option(
        False, "--version", help="Show version and exit", is_eager=True
    ),
):
    if version:
        console.print("gmail-cleanup 0.1.0")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


# ──────────────────────────────────────────────────────────────
# QUERY HELPERS
# ──────────────────────────────────────────────────────────────

def build_query_or_exit(
    *,
    q: str | None,
    from_: str | None,
    to: str | None,
    subject: str | None,
    has_words: str | None,
    not_has_words: str | None,
    label: str | None,
    inbox: bool,
    after: str | None,
    before: str | None,
    older_than: str | None,
    newer_than: str | None,
    has_attachment: bool,
    no_attachment: bool,
    larger: str | None,
    smaller: str | None,
) -> str:
    if has_attachment and no_attachment:
        raise typer.BadParameter("Choose only one: --has-attachment or --no-attachment")

    in_ = "inbox" if inbox else None

    opts = QueryOptions(
        q=q,
        from_=from_,
        to=to,
        subject=subject,
        has_words=has_words,
        not_has_words=not_has_words,
        label=label,
        in_=in_,
        after=after,
        before=before,
        older_than=older_than,
        newer_than=newer_than,
        has_attachment=True if has_attachment else (False if no_attachment else None),
        larger=larger,
        smaller=smaller,
    )

    built = build_query(opts)

    if not built:
        console.print("[bold red]Refusing to run an empty query.[/bold red]")
        console.print("Tip: provide --from, --subject, --older-than, or --q.")
        raise typer.Exit(code=2)

    return built


def build_query_from_locals(d: dict) -> str:
    return build_query_or_exit(
        q=d.get("q"),
        from_=d.get("from_"),
        to=d.get("to"),
        subject=d.get("subject"),
        has_words=d.get("has_words"),
        not_has_words=d.get("not_has_words"),
        label=d.get("label") or d.get("label_filter"),
        inbox=bool(d.get("inbox")),
        after=d.get("after"),
        before=d.get("before"),
        older_than=d.get("older_than"),
        newer_than=d.get("newer_than"),
        has_attachment=bool(d.get("has_attachment")),
        no_attachment=bool(d.get("no_attachment")),
        larger=d.get("larger"),
        smaller=d.get("smaller"),
    )


# ──────────────────────────────────────────────────────────────
# QUERY
# ──────────────────────────────────────────────────────────────

@app.command()
def query(
    q: str = typer.Option(None),
    from_: str = typer.Option(None, "--from"),
    to: str = typer.Option(None),
    subject: str = typer.Option(None),
    has_words: str = typer.Option(None),
    not_has_words: str = typer.Option(None),
    label: str = typer.Option(None),
    inbox: bool = typer.Option(False),
    after: str = typer.Option(None),
    before: str = typer.Option(None),
    older_than: str = typer.Option(None),
    newer_than: str = typer.Option(None),
    has_attachment: bool = typer.Option(False),
    no_attachment: bool = typer.Option(False),
    larger: str = typer.Option(None),
    smaller: str = typer.Option(None),
    sample: int | None = typer.Option(None),
):
    sample = sample if sample is not None else CFG.default_sample
    built = build_query_from_locals(locals())

    console.print("\n[bold]Gmail query:[/bold]")
    console.print(built)

    service = get_gmail_service()

    total = count_messages(service, built)
    with_att = count_messages(service, f"{built} has:attachment")
    without_att = count_messages(service, f"{built} -has:attachment")

    table = Table(title="Query Summary (dry-run)")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    table.add_row("Total", str(total))
    table.add_row("With attachments", str(with_att))
    table.add_row("Without attachments", str(without_att))
    console.print(table)

    if sample > 0 and total > 0:
        rows = sample_messages(service, built, limit=sample)
        st = Table()
        st.add_column("Date")
        st.add_column("From")
        st.add_column("Subject")
        for r in rows:
            st.add_row(r["date"], r["from"], r["subject"])
        console.print(st)


# ──────────────────────────────────────────────────────────────
# LABEL
# ──────────────────────────────────────────────────────────────

@app.command()
def label(
    q: str = typer.Option(None),
    from_: str = typer.Option(None, "--from"),
    to: str = typer.Option(None),
    subject: str = typer.Option(None),
    has_words: str = typer.Option(None),
    not_has_words: str = typer.Option(None),
    label_filter: str = typer.Option(None, "--label"),
    inbox: bool = typer.Option(False),
    after: str = typer.Option(None),
    before: str = typer.Option(None),
    older_than: str = typer.Option(None),
    newer_than: str = typer.Option(None),
    has_attachment: bool = typer.Option(False),
    no_attachment: bool = typer.Option(False),
    larger: str = typer.Option(None),
    smaller: str = typer.Option(None),
    target_label: str | None = typer.Option(None),
    limit: int = typer.Option(0),
):
    target_label = target_label or CFG.default_target_label
    built = build_query_from_locals(locals())

    console.print("\n[bold]Gmail query:[/bold]")
    console.print(built)
    console.print(f"\n[bold]Target label:[/bold] {target_label}")

    service = get_gmail_service()
    label_id = get_or_create_label_id(service, target_label)

    total = count_messages(service, built)
    if total == 0:
        console.print("No matching messages.")
        raise typer.Exit()

    confirm = typer.prompt("Type YES to proceed", default="NO")
    if confirm != "YES":
        raise typer.Exit(code=1)

    done = 0
    for ids in iter_message_id_pages(service, built, limit=limit):
        apply_label_to_messages(service, label_id, ids)
        done += len(ids)
        console.print(f"Labeled {done}/{total if not limit else min(total, limit)}")


# ──────────────────────────────────────────────────────────────
# EXPORT
# ──────────────────────────────────────────────────────────────

@app.command()
def export(
    q: str = typer.Option(None),
    from_: str = typer.Option(None, "--from"),
    to: str = typer.Option(None),
    subject: str = typer.Option(None),
    has_words: str = typer.Option(None),
    not_has_words: str = typer.Option(None),
    label_filter: str = typer.Option(None, "--label"),
    inbox: bool = typer.Option(False),
    after: str = typer.Option(None),
    before: str = typer.Option(None),
    older_than: str = typer.Option(None),
    newer_than: str = typer.Option(None),
    has_attachment: bool = typer.Option(False),
    no_attachment: bool = typer.Option(False),
    larger: str = typer.Option(None),
    smaller: str = typer.Option(None),
    out: Path = typer.Option(Path("reports/report.csv")),
    fmt: str = typer.Option("csv", "--format", help="csv or json"),
    limit: int | None = typer.Option(None),
):
    limit = limit if limit is not None else CFG.default_export_limit
    built = build_query_from_locals(locals())

    service = get_gmail_service()
    total = count_messages(service, built)
    export_n = min(total, limit)

    rows = []
    with Progress() as progress:
        task = progress.add_task("Exporting", total=export_n)
        for ids in iter_message_id_pages(service, built, limit=export_n):
            for msg_id in ids:
                rows.append(fetch_message_row(service, msg_id))
                progress.update(task, advance=1)

    if fmt == "csv":
        write_csv(rows, out)
    else:
        write_json(rows, out)


# ──────────────────────────────────────────────────────────────
# TRASH
# ──────────────────────────────────────────────────────────────

@app.command()
def trash(
    label: str = typer.Option(
        ...,
        "--label",
        help="ONLY trash messages in this label (recommended: cleanup/candidates).",
    ),
    sample: int | None = typer.Option(
        None,
        help="How many sample messages to show before trashing.",
    ),
    execute: bool = typer.Option(
        False,
        "--execute",
        help="Actually perform the trash action.",
    ),
    limit: int = typer.Option(
        0,
        help="Limit how many messages to trash (0 = no limit).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Override safety limit from config.",
    ),
):
    """
    Move messages to Trash. Safety: requires a cleanup/* label and explicit --execute.
    """
    if not label.startswith("cleanup/"):
        console.print(
            "[bold red]Refusing.[/bold red] For safety, --label must start with 'cleanup/'."
        )
        raise typer.Exit(code=2)

    # default sample from config (CLI overrides)
    sample = sample if sample is not None else CFG.default_sample

    built = f"label:{label}"
    console.print("\n[bold]Trash scope query:[/bold]")
    console.print(built)

    service = get_gmail_service()

    total = count_messages(service, built)
    if total == 0:
        console.print("\nNo matching messages. Nothing to trash.")
        raise typer.Exit()

    console.print(f"\nMatched {total} messages in label:{label}")

    if sample > 0:
        console.print("\n[bold]Sample messages:[/bold]")
        rows = sample_messages(service, built, limit=sample)
        st = Table()
        st.add_column("Date")
        st.add_column("From")
        st.add_column("Subject")
        for r in rows:
            st.add_row(r["date"], r["from"], r["subject"])
        console.print(st)

    target_n = min(total, limit) if limit else total

    if target_n > CFG.max_trash_without_force and not force:
        console.print(
            f"[bold red]Refusing.[/bold red] Attempting to trash {target_n} messages, "
            f"but config max_trash_without_force is {CFG.max_trash_without_force}.\n"
            f"Use --force if you are absolutely sure."
        )
        raise typer.Exit(code=2)

    console.print("\n[bold yellow]About to move messages to Trash (recoverable).[/bold yellow]")
    console.print(f"Label: {label}")
    console.print(f"Count: {target_n}")

    if not execute:
        console.print(
            "\nDry-run only. Re-run with [bold]--execute[/bold] to perform trashing."
        )
        raise typer.Exit()

    phrase = f"TRASH {target_n}"
    typed = typer.prompt(f"Type exactly: {phrase}", default="")
    if typed != phrase:
        console.print("Cancelled.")
        raise typer.Exit(code=1)

    done = 0
    for ids in iter_message_id_pages(service, built, limit=target_n):
        trash_message_ids(service, ids)
        done += len(ids)
        console.print(f"Trashed {done}/{target_n}")

    console.print("\nDone. Messages moved to Trash.")


# ──────────────────────────────────────────────────────────────
# DOCTOR
# ──────────────────────────────────────────────────────────────

@app.command()
def doctor():
    console.print(f"OS: {platform.system()} {platform.release()}")
    console.print(f"App data dir:\n  {_app_data_dir()}")
    console.print(f"credentials.json: {credentials_path()}")
    console.print(f"token.json: {token_path()}")
    console.print("Scopes:")
    for s in SCOPES:
        console.print(f"  - {s}")


# ──────────────────────────────────────────────────────────────
# LABEL CLEAR
# ──────────────────────────────────────────────────────────────

@app.command()
@app.command()
def label_clear(
    label: str = typer.Option(..., "--label", help="Label to remove (must start with cleanup/)."),
    limit: int = typer.Option(0, help="Limit how many messages to update (0 = all)."),
):
    service = get_gmail_service()
    label_id = get_or_create_label_id(service, label)
    query = f"label:{label}"

    for ids in iter_message_id_pages(service, query, limit=limit):
        remove_label(service, label_id, ids)


# ──────────────────────────────────────────────────────────────
# STATS
# ──────────────────────────────────────────────────────────────

@app.command()
def stats(
    q: str = typer.Option(None),
    from_: str = typer.Option(None, "--from"),
    to: str = typer.Option(None),
    subject: str = typer.Option(None),
    has_words: str = typer.Option(None),
    not_has_words: str = typer.Option(None),
    label_filter: str = typer.Option(None, "--label"),
    inbox: bool = typer.Option(False),
    after: str = typer.Option(None),
    before: str = typer.Option(None),
    older_than: str = typer.Option(None),
    newer_than: str = typer.Option(None),
    has_attachment: bool = typer.Option(False),
    no_attachment: bool = typer.Option(False),
    larger: str = typer.Option(None),
    smaller: str = typer.Option(None),
    scan_limit: int | None = typer.Option(None),
    top: int = typer.Option(10),
):
    scan_limit = scan_limit if scan_limit is not None else CFG.default_scan_limit
    built = build_query_from_locals(locals())

    service = get_gmail_service()
    senders, oldest, newest = collect_sender_counts_and_dates(
        service, built, scan_limit=scan_limit
    )

    table = Table(title="Top senders")
    table.add_column("Sender")
    table.add_column("Count", justify="right")
    for sender, cnt in senders.most_common(top):
        table.add_row(sender, str(cnt))
    console.print(table)


# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────

@app.command()
def config(init: bool = typer.Option(False)):
    path = config_path()
    if init:
        write_template(overwrite=False)

    cfg = load_config()
    console.print(f"Config file: {path}")
    console.print(f"default_target_label: {cfg.default_target_label}")
    console.print(f"max_trash_without_force: {cfg.max_trash_without_force}")
    console.print(f"default_export_limit: {cfg.default_export_limit}")
    console.print(f"default_scan_limit: {cfg.default_scan_limit}")
    console.print(f"default_sample: {cfg.default_sample}")
