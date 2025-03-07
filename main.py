
from options import get_options
from log_config import setup_logging
import logging
from tuegist import TueGist

log = logging.getLogger(__name__)
setup_logging()


def main():
    args = get_options()
    tuegist = TueGist()
    
    if args.rebuild:
        # Rebuild everything
        tuegist.rebuild()

    elif args.pages:
        # Rebuild pages
        tuegist.build_pages()

    elif args.gists:
        # Rebuild gists
        tuegist.build_gists()

    elif args.index:
        # Rebuild index
        tuegist.build_index()
        
    elif args.scan:
        # Scan gists
        tuegist.scan()
        
    elif args.tues:
        # Perform weekly post actions
        tuegist.tues()

if __name__ == "__main__":
    main()
