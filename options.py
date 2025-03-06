import argparse

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='TueGist - A static site generator for GitHub gists'
    )

    # Add arguments
    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Rebuild all pages & gists from the DB'
    )

    parser.add_argument(
        '--pages',
        action='store_true',
        help='Rebuild the static pages (index, about, contact, rss)'
    )

    parser.add_argument(
        '--gists',
        action='store_true',
        help='Rebuild all gists'
    )

    parser.add_argument(
        '--index',
        action='store_true',
        help='Rebuild the index.html and rss.xml files'
    )

    parser.add_argument(
        '--scan',
        action='store_true',
        help='Scan gists and update the DB without rebuilding HTML files'
    )

    parser.add_argument(
        '--tues',
        action='store_true',
        help='Perform weekly post actions'
    )


    args = parser.parse_args()
    return args

def validate_args(args):
    """Validate the parsed arguments and set defaults if needed."""
    # If no action arguments are specified, default to --rebuild
    if not any([args.rebuild, args.pages, args.gists, args.index, args.scan, args.tues]):
        args.tues = True
    
    return args

def get_options():
    """Get and validate command line options."""
    args = parse_args()
    return validate_args(args) 