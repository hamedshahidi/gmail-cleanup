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
from gmail_cleanup.query_builder import QueryOptions, build_query
from gmail_cleanup.labels import get_or_create_label_id, apply_label_to_messages
from gmail_cleanup.exporter import fetch_message_row, write_csv, write_json
from gmail_cleanup.trash import trash_message_ids
from gmail_cleanup.label_clear import remove_label
from gmail_cleanup.stats import collect_sender_counts_and_dates
from gmail_cleanup.config import load_config, config_path, write_template
from gmail_cleanup.gmail_iter import iter_message_id_pages

CFG = load_config()
console = Console()
app = typer.Typer(add_completion=False, invoke_without_command=True)


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
# QUERY
# ──────────────────────────────────────────────────────────────

@app.command()
def query(
    q: str = typer.Option(None, help="Raw Gmail query (advanced)."),
    from_: str = typer.Option(None, "--from", help="Sender email/address."),
    to: str = typer.Option(None, help="Recipient email/address."),
    subject: str = typer.Option(None, help="Subject contains."),
    has_words: str = typer.Option(None, help="Has these words."),
    not_has_words: str = typer.Option(None, help="Does NOT have these words."),
    label: str = typer.Option(None, help="Gmail label."),
    inbox: bool = typer.Option(False, help="Shortcut for in:inbox"),
    after: str = typer.Option(None, help="After date YYYY/MM/DD"),
    before: str = typer.Option(None, help="Before date YYYY/MM/DD"),
    older_than: str = typer.Option(None, help="e.g. 30d, 12m, 2y"),
    newer_than: str = typer.Option(None, help="e.g. 7d"),
    has_attachment: bool = typer.Option(False, help="Only emails WITH attachments."),
    no_attachment: bool = typer.Option(False, help="Only emails WITHOUT attachments."),
    larger: str = typer.Option(None, help="Message larger than, e.g. 10M"),
    smaller: str = typer.Option(None, help="Message smaller than, e.g. 2M"),
    sample: int | None = typer.Option(None, help="How many sample messages to show."),
):
    """
    Dry-run: show counts and samples for a query. No deletion.
    """
    if has_attachment and no_attachment:
        raise typer.BadParameter("Choose only one: --has-attachment or --no-attachment")

    sample = sample if sample is not None else CFG.default_sample
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

    console.print("\n[bold]Gmail query:[/bold]")
    console.print(built)

    service = get_gmail_service()

    console.print("\n[bold]Counting...[/bold]")
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
        console.print("\n[bold]Sample messages:[/bold]")
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
    q: str = typer.Option(None, help="Raw Gmail query (advanced)."),
    from_: str = typer.Option(None, "--from", help="Sender email/address."),
    to: str = typer.Option(None, help="Recipient email/address."),
    subject: str = typer.Option(None, help="Subject contains."),
    has_words: str = typer.Option(None, help="Has these words."),
    not_has_words: str = typer.Option(None, help="Does NOT have these words."),
    label_filter: str = typer.Option(
        None, "--label", help="Filter: only messages already in this Gmail label."
    ),
    inbox: bool = typer.Option(False, help="Shortcut for in:inbox"),
    after: str = typer.Option(None, help="After date YYYY/MM/DD"),
    before: str = typer.Option(None, help="Before date YYYY/MM/DD"),
    older_than: str = typer.Option(None, help="e.g. 30d, 12m, 2y"),
    newer_than: str = typer.Option(None, help="e.g. 7d"),
    has_attachment: bool = typer.Option(False, help="Only emails WITH attachments."),
    no_attachment: bool = typer.Option(False, help="Only emails WITHOUT attachments."),
    larger: str = typer.Option(None, help="Message larger than, e.g. 10M"),
    smaller: str = typer.Option(None, help="Message smaller than, e.g. 2M"),
    target_label: str | None = typer.Option(
        None, help="Label to apply to matched messages."
    ),
    limit: int = typer.Option(0, help="Limit how many messages to label (0 = no limit)."),
):
    """
    Staging mode: apply a label to all messages that match a query. No deletion.
    """
    if has_attachment and no_attachment:
        raise typer.BadParameter("Choose only one: --has-attachment or --no-attachment")

    target_label = target_label or CFG.default_target_label
    in_ = "inbox" if inbox else None

    opts = QueryOptions(
        q=q,
        from_=from_,
        to=to,
        subject=subject,
        has_words=has_words,
        not_has_words=not_has_words,
        label=label_filter,
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
        raise typer.Exit(code=2)

    console.print("\n[bold]Gmail query:[/bold]")
    console.print(built)
    console.print(f"\n[bold]Target label:[/bold] {target_label}")

    service = get_gmail_service()
    label_id = get_or_create_label_id(service, target_label)

    total = count_messages(service, built)
    if total == 0:
        console.print("\nNo matching messages. Nothing to label.")
        raise typer.Exit()

    console.print(
        f"\nFound {total} messages. This will APPLY label '{target_label}' (no deletion)."
    )
    confirm = typer.prompt("Type YES to proceed", default="NO")
    if confirm != "YES":
        console.print("Cancelled.")
        raise typer.Exit(code=1)

    done = 0
    for ids in iter_message_id_pages(service, built, limit=limit):
        apply_label_to_messages(service, label_id, ids)
        done += len(ids)
        console.print(f"Labeled {done}/{total if not limit else min(total, limit)}")

    console.print("\nDone. Review the label in Gmail before deleting anything.")


# ──────────────────────────────────────────────────────────────
# EXPORT
# ──────────────────────────────────────────────────────────────

@app.command()
def export(
    q: str = typer.Option(None, help="Raw Gmail query (advanced)."),
    from_: str = typer.Option(None, "--from", help="Sender email/address."),
    to: str = typer.Option(None, help="Recipient email/address."),
    subject: str = typer.Option(None, help="Subject contains."),
    has_words: str = typer.Option(None, help="Has these words."),
    not_has_words: str = typer.Option(None, help="Does NOT have these words."),
    label_filter: str = typer.Option(
        None, "--label", help="Filter: only messages already in this Gmail label."
    ),
    inbox: bool = typer.Option(False, help="Shortcut for in:inbox"),
    after: str = typer.Option(None, help="After date YYYY/MM/DD"),
    before: str = typer.Option(None, help="Before date YYYY/MM/DD"),
    older_than: str = typer.Option(None, help="e.g. 30d, 12m, 2y"),
    newer_than: str = typer.Option(None, help="e.g. 7d"),
    has_attachment: bool = typer.Option(False, help="Only emails WITH attachments."),
    no_attachment: bool = typer.Option(False, help="Only emails WITHOUT attachments."),
    larger: str = typer.Option(None, help="Message larger than, e.g. 10M"),
    smaller: str = typer.Option(None, help="Message smaller than, e.g. 2M"),
    out: Path = typer.Option(Path("reports/report.csv"), help="Output file path."),
    fmt: str = typer.Option("csv", "--format", help="csv or json"),
    limit: int | None = typer.Option(None, help="Max messages to export"),
):
    """
    Export a report of matched emails (metadata only). No deletion.
    """
    if has_attachment and no_attachment:
        raise typer.BadParameter("Choose only one: --has-attachment or --no-attachment")

    limit = limit if limit is not None else CFG.default_export_limit
    in_ = "inbox" if inbox else None

    opts = QueryOptions(
        q=q,
        from_=from_,
        to=to,
        subject=subject,
        has_words=has_words,
        not_has_words=not_has_words,
        label=label_filter,
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
        raise typer.Exit(code=2)

    fmt = fmt.strip().lower()
    if fmt not in ("csv", "json"):
        raise typer.BadParameter("--format must be csv or json")

    if limit < 1:
        raise typer.BadParameter("--limit must be >= 1")

    console.print("\n[bold]Gmail query:[/bold]")
    console.print(built)

    service = get_gmail_service()
    total = count_messages(service, built)
    if total == 0:
        console.print("\nNo matching messages. Nothing to export.")
        raise typer.Exit()

    export_n = min(total, limit)
    console.print(
        f"\nExporting {export_n} of {total} messages to: [bold]{out}[/bold] ({fmt})"
    )

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

    console.print("\nDone.")


# ──────────────────────────────────────────────────────────────
# TRASH
# ──────────────────────────────────────────────────────────────

@app.command()
def trash(
    label: str = typer.Option(
        ..., help="ONLY trash messages in this label (recommended: cleanup/candidates)."
    ),
    sample: int = typer.Option(10, help="How many sample messages to show before trashing."),
    execute: bool = typer.Option(False, "--execute", help="Actually perform the trash action."),
    limit: int = typer.Option(0, help="Limit how many messages to trash (0 = no limit)."),
    force: bool = typer.Option(False, "--force", help="Override safety limit from config."),
):
    """
    Move messages to Trash. Safety: requires a cleanup/* label and explicit --execute.
    """
    if not label.startswith("cleanup/"):
        console.print(
            "[bold red]Refusing.[/bold red] For safety, --label must start with 'cleanup/'."
        )
        raise typer.Exit(code=2)

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
        console.print("\nDry-run only. Re-run with [bold]--execute[/bold] to perform trashing.")
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
    """
    Diagnose local setup and OAuth configuration.
    """
    console.print("\n[bold]gmail-cleanup doctor[/bold]\n")

    console.print(f"OS: {platform.system()} {platform.release()}")
    console.print(f"App data dir:\n  {_app_data_dir()}\n")

    cred = credentials_path()
    tok = token_path()

    def status(path):
        return "[green]OK[/green]" if path.exists() else "[red]MISSING[/red]"

    console.print("Credentials:")
    console.print(f"  credentials.json: {cred}  → {status(cred)}")
    console.print("\nAuth token:")
    console.print(f"  token.json:        {tok}   → {status(tok)}")

    if not cred.exists():
        console.print(
            "\n[yellow]How to fix:[/yellow]\n"
            "1) Create a Google Cloud project\n"
            "2) Enable Gmail API\n"
            "3) Create OAuth client (Desktop app)\n"
            "4) Download credentials.json\n"
            f"5) Copy it to:\n   {cred}\n"
        )

    console.print("\nOAuth scopes in use:")
    for s in SCOPES:
        console.print(f"  - {s}")

    console.print("\n[dim]No changes were made.[/dim]")


# ──────────────────────────────────────────────────────────────
# LABEL CLEAR (command name shows as label-clear)
# ──────────────────────────────────────────────────────────────

@app.command()
def label_clear(
    label: str = typer.Option(..., help="Label to remove (must start with cleanup/)."),
    limit: int = typer.Option(0, help="Limit how many messages to update (0 = all)."),
):
    """
    Remove a cleanup/* label from messages (undo staging).
    """
    if not label.startswith("cleanup/"):
        console.print("[bold red]Refusing.[/bold red] Label must start with 'cleanup/'.")
        raise typer.Exit(code=2)

    service = get_gmail_service()
    label_id = get_or_create_label_id(service, label)

    query = f"label:{label}"
    total = count_messages(service, query)
    if total == 0:
        console.print("No messages found with that label.")
        raise typer.Exit()

    target_n = min(total, limit) if limit else total
    console.print(f"Removing label '{label}' from {target_n} messages.")

    done = 0
    for ids in iter_message_id_pages(service, query, limit=target_n):
        remove_label(service, label_id, ids)
        done += len(ids)
        console.print(f"Updated {done}/{target_n}")

    console.print("Done.")


# ──────────────────────────────────────────────────────────────
# STATS
# ──────────────────────────────────────────────────────────────

@app.command()
def stats(
    q: str = typer.Option(None, help="Raw Gmail query (advanced)."),
    from_: str = typer.Option(None, "--from", help="Sender email/address."),
    to: str = typer.Option(None, help="Recipient email/address."),
    subject: str = typer.Option(None, help="Subject contains."),
    has_words: str = typer.Option(None, help="Has these words."),
    not_has_words: str = typer.Option(None, help="Does NOT have these words."),
    label_filter: str = typer.Option(None, "--label", help="Filter: only messages already in this Gmail label."),
    inbox: bool = typer.Option(False, help="Shortcut for in:inbox"),
    after: str = typer.Option(None, help="After date YYYY/MM/DD"),
    before: str = typer.Option(None, help="Before date YYYY/MM/DD"),
    older_than: str = typer.Option(None, help="e.g. 30d, 12m, 2y"),
    newer_than: str = typer.Option(None, help="e.g. 7d"),
    has_attachment: bool = typer.Option(False, help="Only emails WITH attachments."),
    no_attachment: bool = typer.Option(False, help="Only emails WITHOUT attachments."),
    larger: str = typer.Option(None, help="Message larger than, e.g. 10M"),
    smaller: str = typer.Option(None, help="Message smaller than, e.g. 2M"),
    scan_limit: int | None = typer.Option(None, help="How many messages to scan (sample-based)."),
    top: int = typer.Option(10, help="How many top senders to display."),
):
    if has_attachment and no_attachment:
        raise typer.BadParameter("Choose only one: --has-attachment or --no-attachment")

    scan_limit = scan_limit if scan_limit is not None else CFG.default_scan_limit
    in_ = "inbox" if inbox else None

    opts = QueryOptions(
        q=q,
        from_=from_,
        to=to,
        subject=subject,
        has_words=has_words,
        not_has_words=not_has_words,
        label=label_filter,
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
        raise typer.Exit(code=2)

    console.print("\n[bold]Gmail query:[/bold]")
    console.print(built)

    service = get_gmail_service()
    total = count_messages(service, built)
    console.print(f"\nTotal matches: [bold]{total}[/bold]")

    if total == 0:
        raise typer.Exit()

    scan_n = min(total, scan_limit)
    console.print(f"Scanning first {scan_n} message(s) for stats...")

    senders, oldest, newest = collect_sender_counts_and_dates(service, built, scan_limit=scan_n)

    if oldest and newest:
        console.print(f"\nDate range (sampled):\n  oldest: {oldest}\n  newest: {newest}")

    st = Table(title=f"Top senders (based on first {scan_n})")
    st.add_column("Sender")
    st.add_column("Count", justify="right")
    for sender, cnt in senders.most_common(top):
        st.add_row(sender, str(cnt))
    console.print()
    console.print(st)


# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────

@app.command()
def config(
    init: bool = typer.Option(False, "--init", help="Create config.yaml template (won't overwrite).")
):
    """
    Show config location and currently loaded config values.
    """
    path = config_path()
    if init:
        created = write_template(overwrite=False)
        console.print(f"Config template ensured at:\n  {created}")

    cfg = load_config()
    console.print("\n[bold]Config file:[/bold]")
    console.print(f"  {path}")
    console.print("\n[bold]Loaded config:[/bold]")
    console.print(f"  default_target_label: {cfg.default_target_label}")
    console.print(f"  max_trash_without_force: {cfg.max_trash_without_force}")
    console.print(f"  default_export_limit: {cfg.default_export_limit}")
    console.print(f"  default_scan_limit: {cfg.default_scan_limit}")
    console.print(f"  default_sample: {cfg.default_sample}")
