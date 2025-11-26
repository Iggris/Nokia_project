import argparse
import os
import sys
from file_scanner import FileScanner
from file_regex.file_regex import FileRegex


def match_to_string(pattern_id, start, end, filename):
    with open(filename, "r") as f:
        f.seek(start)
        match = f.read(end - start)
    return f"Regex with ID: {pattern_id}, filename: '{filename}', from: {start} end: {end}, match: '{match}'"


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build
    build = subparsers.add_parser("build")

    build.add_argument(
        "source",
        help="text file with regexes (one regex per line)"
    )

    build.add_argument(
        "-o", "--output",
        default="hs.db",
        help="output file (default hs.db)"
    )

    # run
    run = subparsers.add_parser("run")

    run.add_argument(
        "config",
        help="either a compiled Hyperscan database (created by "
             "build command) or a text file with regexes (one per "
             "line)"
    )

    run.add_argument(
        "target",
        help="file or directory to scan"
    )

    run.add_argument(
        "-o", "--output",
        required=False,
        help="save results to file (default: stdout)"
    )

    args = parser.parse_args()

    if args.command == "run":
        scanner = FileScanner()

        try:
            scanner.engine.load_db(args.config)
        except Exception:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))

            fr = FileRegex(args.config)
            patterns = fr.elements()
            scanner.compile_patterns(patterns)

        results = []

        if os.path.isfile(args.target):
            results = scanner.scan_file(args.target)

        elif os.path.isdir(args.target):
            results = scanner.scan_tree(args.target)
        else:
            print(f"cannot access '{args.target}': No such file or directory")

        if args.output is None:
            out = sys.stdout
        else:
            out = open(args.output, "w")

        for result in results:
            match = match_to_string(result['pattern_id'], result['start'],
                                    result['end'], result['filename'])
            print(match, file=out)

        if out is not sys.stdout:
            out.close()

    elif args.command == "build":
        fr = FileRegex(args.source)
        patterns = fr.elements()

        scanner = FileScanner()
        scanner.compile_patterns(patterns)

        scanner.engine.save_db(args.output)


if __name__ == "__main__":
    main()
