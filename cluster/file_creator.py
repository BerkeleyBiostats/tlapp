import os
from django.template import loader


class FileCreator(object):

    directory = None

    def initialize(self, directory):
        self.directory = directory
        if not os.path.exists(directory):
            os.makedirs(directory)


    def create_file(self, name=None, content=None, copy_from_path=None, template=None, template_params=None, executable=False):
        if copy_from_path:
            with open(copy_from_path) as f:
                content = f.read()
        if template:
            template = loader.get_template(template)
            content = template.render(template_params)
        filename = os.path.join(self.directory, name)
        with open(filename, "w") as f:
            f.write(content)
        if executable:
            os.chmod(filename, 0o755)

    def create_directory(self, name=None):
        path = os.path.join(self.directory, name)
        os.mkdir(path)