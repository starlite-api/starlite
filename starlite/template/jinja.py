from typing import List, Union

from pydantic import DirectoryPath

from starlite.exceptions import TemplateNotFound
from starlite.extras import JINJA
from starlite.template.base import TemplateEngineProtocol

with JINJA:
    # pylint: disable=import-error
    from jinja2 import Environment, FileSystemLoader
    from jinja2 import Template as JinjaTemplate
    from jinja2 import TemplateNotFound as JinjaTemplateNotFound


class JinjaTemplateEngine(TemplateEngineProtocol[JinjaTemplate]):
    """Template engine using the jinja templating library"""

    def __init__(self, directory: Union[DirectoryPath, List[DirectoryPath]]) -> None:
        super().__init__(directory)
        loader = FileSystemLoader(searchpath=directory)
        self.engine = Environment(loader=loader, autoescape=True)

    def get_template(self, name: str) -> JinjaTemplate:
        """Loads the template with the name and returns it."""
        try:
            return self.engine.get_template(name=name)
        except JinjaTemplateNotFound as e:
            raise TemplateNotFound(template_name=name) from e
