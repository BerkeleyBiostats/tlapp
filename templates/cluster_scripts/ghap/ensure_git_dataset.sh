
REPO_BASE_PATH={{ repo_base_path}}
REPO_PATH={{ repo_path }}

if [ ! -d $REPO_PATH]; then

    cd $REPO_BASE_PATH

    # Hide sensitive ouput
    git clone {{ git_url_with_password }} > /dev/null

fi
