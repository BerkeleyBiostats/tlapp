
def expand_r_package_definition(package_definition):
    if package_definition.startswith("github://"):
        full_package_name = package_definition[len("github://") :]
        package_name = full_package_name.split("/")[-1]
        output = "R -e \"devtools::install_github('%s')\"" % (full_package_name)
    elif "@" in package_definition:
        package_name, version = package_definition.split("@")
        output = (
            "R -e \"if (!require('%s')) devtools::install_version('%s', version='%s', repos = 'http://cran.rstudio.com/')\""
            % (package_name, package_name, version)
        )
    else:
        package_name = package_definition
        output = (
            "R -e \"if (!require('%s')) install.packages('%s', repos = 'http://cran.rstudio.com/')\""
            % (package_name, package_name)
        )

    return output


def build_provision_code(r_packages_section, backend=None):

    preamble = ""

    if backend == "ghap":
        preamble = """

mkdir -p "/data/R/x86_64-redhat-linux-gnu-library/3.2/"
mkdir -p "/data/R/x86_64-redhat-linux-gnu-library/3.4/"

"""
    elif backend == "bluevelvet":
        preamble = """

module load pandoc-2.1.2
module load gcc-4.9.4
module load python-3.5.2

"""

    return preamble + "\n".join(
        [expand_r_package_definition(pd) for pd in r_packages_section]
    )