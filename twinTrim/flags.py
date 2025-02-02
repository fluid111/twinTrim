import os
import click
import time
import logging
from collections import defaultdict
from twinTrim.utils import handle_and_remove, parse_size
from twinTrim.flagController import handleAllFlag, find_duplicates
from beaupy import select_multiple
from twinTrim.dataStructures.fileFilter import FileFilter

#Setting up logging configuration
logging.basicConfig (
    filename='duplicate_file_manager.log',   #log the file name
    level = logging.INFO,                    #Set the logging level
    format = '%(asctime)s - %(levelname)s - %(message)s'       #log message format                                    
)

@click.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--all", is_flag=True, help="Delete duplicates automatically without asking.")
@click.option("--min-size", default="0kb", type=str, help="Minimum file size in bytes.")
@click.option("--max-size", default="1gb", type=str, help="Maximum file size in bytes.")
@click.option("--file-type", default=".*", help="File type to include (e.g., .txt, .jpg).")
@click.option("--exclude", multiple=True, help="Files to exclude by name.")
@click.option("--label-color", default="yellow", type=str, help="Color of the label of progress bar.")
@click.option("--bar-color", default='#aaaaaa', type=str, help="Color of the progress bar.")
def cli(directory, all, min_size, max_size, file_type, exclude, label_color, bar_color):
    """Find and manage duplicate files in the specified DIRECTORY."""

    # Initialize the FileFilter object
    file_filter = FileFilter()
    file_filter.setMinFileSize(parse_size(min_size))
    file_filter.setMaxFileSize(parse_size(max_size))
    file_filter.setFileType(file_type)
    for file_name in exclude:
        file_filter.addFileExclude(file_name)

    if all:
        logging.info("Deleting all duplicate files whithout asking.")
        handleAllFlag(directory, file_filter, label_color, bar_color)
        return

    start_time = time.time()
    logging.info(f"Searching for duplicates in directory: {directory}")
    
    try:
        duplicates = find_duplicates(directory, file_filter, label_color, bar_color)
    except Exception as e:
        logging.error(f"Error finding duplicates: {str(e)}")
        click.echo(click.style("Error while finding duplicates. Check the log for details.", fg='red'))
        return


    if not duplicates:
        click.echo(click.style("No duplicate files found.", fg='green'))
        logging.info("No duplicate files found.")
        return

    click.echo(click.style(f"Found {len(duplicates)} sets of duplicate files:", fg='yellow'))
    logging.info(f"Found {len(duplicates)} set of duplicate files")

    duplicates_dict = defaultdict(list)
    for original, duplicate in duplicates:
        duplicates_dict[original].append(duplicate)

    # Process each set of duplicates
    for original, duplicates_list in duplicates_dict.items():
        click.echo(click.style(f"Original file: \"{original}\"", fg='cyan'))
        click.echo(click.style(f"Number of duplicate files found: {len(duplicates_list)}", fg='cyan'))
        logging.info(f"Original file: \"{original}\" with {len(duplicates_list)} duplicates")

        click.echo(click.style("They are:", fg='cyan'))
        file_options = [f"{idx + 1}) {duplicate}" for idx, duplicate in enumerate(duplicates_list)]
        
        # Prompt user to select which files to delete
        selected_indices = select_multiple(
            file_options,  # List of files to choose from
            ticked_indices=[],         # Default indices that are selected
            maximal_count=len(file_options)  
        )

        # Convert the indices back to the original file paths
        files_to_delete = [duplicates_list[int(option.split(")")[0]) - 1] for option in selected_indices]

        for file_path in files_to_delete:
            try:
                handle_and_remove(file_path)
                logging.info(f"Deleted duplicate file: {file_path}")
            except Exception as e:
                logging.error(f"Error deleting file {file_path}: {str(e)}")
                click.echo(click.style(f"Error deleting file: {file_path}. Check the log for details.", fg='red'))


    end_time = time.time()
    time_taken = end_time - start_time
    click.echo(click.style(f"Time taken: {time_taken:.2f} seconds.", fg='green'))
    logging.info(f"Total time taken: {time_taken:.2f} seconds.")

if __name__ == "__main__":
    cli()
