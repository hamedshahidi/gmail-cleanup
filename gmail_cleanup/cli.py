import click
import typer
from rich.console import Console
from rich.table import Table

from gmail_cleanup.gmail import get_gmail_service
from gmail_cleanup.preview import count_messages, sample_messages
from gmail_cleanup.query_builder import QueryOptions, build_query

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
    sample: int = typer.Option(10, help="How many sample messages to show."),
):
    """
    Dry-run: show counts and samples for a query. No deletion.
    """
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
