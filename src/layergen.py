import os
import re
import shutil
import subprocess
import sys
import uuid

import click


# Helper functions
def check_dependencies():
    """Check if AWS CLI, pip, zip, and npm are installed."""
    has_aws = True
    has_pip = True
    has_npm = True

    if shutil.which("aws") is None:
        has_aws = False

    if shutil.which("pip") is None:
        has_pip = False

    if shutil.which("npm") is None:
        has_npm = False

    if not has_aws:
        click.echo("Please install the AWS CLI before running this script.")
        sys.exit(1)

    if not has_pip:
        click.echo("Please install pip before running this script.")
        sys.exit(1)

    if not has_npm:
        click.echo("Please install npm before running this script.")
        sys.exit(1)


def check_aws_signed_in():
    """Check if the user is signed in to AWS CLI."""
    try:
        subprocess.run(
            ["aws", "sts", "get-caller-identity"], check=True, capture_output=True
        )
    except subprocess.CalledProcessError:
        click.echo("Please sign in to the AWS CLI before running this script.")
        sys.exit(1)


def get_default_region():
    """Get the default AWS region from the AWS CLI configuration."""
    result = subprocess.run(
        ["aws", "configure", "get", "region"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


# Main CLI Group
@click.group()
def cli():
    """A CLI tool to manage AWS Lambda Layers."""
    pass


# Create command
@cli.command()
@click.option(
    "--layer-name",
    prompt="Enter the AWS Lambda Layer name",
    help="The name of the AWS Lambda Layer.",
)
@click.option(
    "--runtime",
    type=click.Choice(["nodejs", "python"], case_sensitive=False),
    prompt="Select the runtime",
    help="The runtime environment for the Lambda Layer.",
)
@click.option(
    "--packages",
    prompt="Enter the packages you want to include (space-separated)",
    help="Packages to include in the Lambda Layer.",
)
@click.option(
    "--region",
    help="AWS region to upload the Lambda Layer to (default: AWS configured region).",
)
def create(layer_name, runtime, packages, region):
    """Create and upload an AWS Lambda Layer."""
    check_dependencies()
    check_aws_signed_in()

    # Validate layer_name
    if not re.match(r"^[a-zA-Z0-9-]+$", layer_name):
        click.echo("Error: Layer name can only contain letters, numbers, and dashes.")
        sys.exit(1)

    if runtime == "nodejs":
        click.echo("You selected Node.js 20.x")
        runtime_version = "nodejs20.x"
        runtime_dir = "nodejs"
    elif runtime == "python":
        click.echo("You selected Python 3.12")
        runtime_version = "python3.12"
        runtime_dir = "python"

    if region == "None":
        region = get_default_region()

    unique_id = str(uuid.uuid4())
    temp_dir = f"/tmp/layergen/{unique_id}"
    os.makedirs(temp_dir, exist_ok=True)

    os.makedirs(f"{temp_dir}/{runtime_dir}", exist_ok=True)

    try:
        if runtime == "nodejs":
            os.makedirs(f"{temp_dir}/{runtime_dir}/node_modules", exist_ok=True)
            click.echo("Installing npm packages")
            subprocess.run(
                ["npm", "install", "--prefix", f"{temp_dir}/{runtime_dir}"]
                + packages.split(),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            click.echo("Installing pip packages")
            subprocess.run(
                ["pip", "install", "--target", f"{temp_dir}/{runtime_dir}"]
                + packages.split(),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        click.echo(f"Installed packages: {packages}")

        zip_file = f"{temp_dir}/{layer_name}.zip"
        shutil.make_archive(f"{temp_dir}/{layer_name}", "zip", temp_dir)

        if not os.path.exists(zip_file):
            click.echo("Zip file was not created.")
            sys.exit(1)

        click.echo(f"Uploading Lambda Layer from {zip_file}")

        subprocess.run(
            [
                "aws",
                "lambda",
                "publish-layer-version",
                "--layer-name",
                layer_name,
                "--zip-file",
                f"fileb://{zip_file}",
                "--compatible-runtimes",
                runtime_version,
                "--region",
                region,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        click.echo(
            f"Layer {layer_name} has been successfully created and uploaded to AWS Lambda in {region}."
        )
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: {e.stderr or e.output}")
        sys.exit(1)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# List command
@cli.command()
@click.option(
    "--region",
    help="AWS region to list Lambda layers from (default: AWS configured region).",
)
def list(region):
    """List all AWS Lambda Layers."""
    check_dependencies()
    check_aws_signed_in()

    if region is None:
        region = get_default_region()

    if region is None:
        click.echo(
            "Error: No AWS region specified. Please set AWS_DEFAULT_REGION or configure your AWS CLI."
        )
        sys.exit(1)

    result = subprocess.run(
        ["aws", "lambda", "list-layers", "--region", region],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        click.echo("Error listing layers.")
    else:
        click.echo(result.stdout)


@cli.command()
@click.option(
    "--layer-name",
    prompt="Enter the AWS Lambda Layer name",
    help="The name of the AWS Lambda Layer to delete.",
)
@click.option(
    "--version-number",
    prompt="Enter the version number to delete",
    help="The version number of the layer to delete.",
)
@click.option(
    "--region",
    help="AWS region to delete the Lambda Layer from (default: AWS configured region).",
)
def delete(layer_name, version_number, region):
    """Delete an AWS Lambda Layer."""
    check_dependencies()
    check_aws_signed_in()

    if region is None:
        region = get_default_region()

    if region is None:
        click.echo(
            "Error: No AWS region specified. Please set AWS_DEFAULT_REGION or configure your AWS CLI."
        )
        return

    try:
        subprocess.run(
            [
                "aws",
                "lambda",
                "delete-layer-version",
                "--layer-name",
                layer_name,
                "--version-number",
                version_number,
                "--region",
                region,
            ],
            check=True,
        )
        click.echo(f"Layer {layer_name} version {version_number} has been deleted.")
    except subprocess.CalledProcessError:
        click.echo("Error deleting the layer.")
        return


if __name__ == "__main__":
    cli()
