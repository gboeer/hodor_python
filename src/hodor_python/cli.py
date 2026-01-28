import argparse
import sys
from pathlib import Path

from hodor_python.dataset import HODOR_Dataset


DEFAULT_LIST_COLUMNS = [
    "SeqID",
    "DateTimeStart",
    "DateTimeEnd",
    "sequence_length",
]


def _parse_columns(value: str) -> list[str]:
    value = value.strip()
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _select_columns(df, columns: list[str]):
    if not columns:
        return df
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(
            "Unknown columns: "
            + ", ".join(missing)
            + ". Available: "
            + ", ".join(df.columns)
        )
    return df[columns]


def _print_df(df):
    print(df.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hodor-python",
        description="CLI for downloading and inspecting the HODOR dataset.",
    )
    parser.add_argument(
        "--dataset-folder",
        default="hodor_data",
        help="Local folder for cached downloads (default: ./hodor_data).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser(
        "download", help="Download video and/or sonar for sequence IDs."
    )
    download.add_argument("sequence_ids", nargs="+", type=int)
    download.add_argument(
        "--video", action="store_true", help="Download only video data."
    )
    download.add_argument(
        "--sonar", action="store_true", help="Download only sonar data."
    )

    list_cmd = subparsers.add_parser(
        "list", help="List sequences with basic metadata columns."
    )
    list_cmd.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of rows displayed.",
    )
    list_cmd.add_argument(
        "--columns",
        type=_parse_columns,
        default=None,
        help="Comma-separated column list (default: common metadata columns).",
    )

    info = subparsers.add_parser(
        "info", help="Show metadata and counts for a single sequence ID."
    )
    info.add_argument("sequence_id", type=int)

    counts = subparsers.add_parser(
        "counts", help="Output the full counts table."
    )
    counts.add_argument(
        "--output",
        help="Write counts to a file instead of stdout.",
    )
    counts.add_argument(
        "--format",
        choices=["csv", "tsv", "json"],
        default="csv",
        help="Output format when writing to a file (default: csv).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    dataset = HODOR_Dataset(dataset_folder=Path(args.dataset_folder))

    if args.command == "download":
        if args.video and not args.sonar:
            dataset.download_video(args.sequence_ids)
        elif args.sonar and not args.video:
            dataset.download_sonar(args.sequence_ids)
        else:
            dataset.download_sequence(args.sequence_ids)
        return 0

    if args.command == "list":
        df = dataset.counts
        columns = args.columns
        if columns is None:
            columns = DEFAULT_LIST_COLUMNS
        try:
            df = _select_columns(df, columns)
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if args.limit is not None:
            df = df.head(args.limit)
        _print_df(df)
        return 0

    if args.command == "info":
        df = dataset.counts
        row = df[df["SeqID"] == args.sequence_id]
        if row.empty:
            print(f"Sequence {args.sequence_id} not found.", file=sys.stderr)
            return 1
        print(row.iloc[0].to_string())
        return 0

    if args.command == "counts":
        df = dataset.counts
        if args.output:
            output = Path(args.output)
            if args.format == "csv":
                df.to_csv(output, index=False)
            elif args.format == "tsv":
                df.to_csv(output, index=False, sep="\t")
            elif args.format == "json":
                df.to_json(output, orient="records")
        else:
            _print_df(df)
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
