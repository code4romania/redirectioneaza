from typing import Callable, Dict, List, Optional, Union

from django.db.models import QuerySet


class QueryFilter:
    id: str = None
    key: str = None
    type: str = None

    title: str = None

    queryset_key: str = None
    queryset_transformation: Optional[Callable] = None

    def options(self, objects: Optional[QuerySet] = None) -> List[Dict[str, Union[int, str]]]:
        if objects is None:
            return self.options_default()

        try:
            return self.options_with_objects(objects)
        except NotImplementedError:
            return self.options_default()

    def options_with_objects(self, objects: QuerySet) -> List[Dict[str, Union[int, str]]]:
        raise NotImplementedError("Options method must be implemented in subclass")

    def options_default(self) -> List[Dict[str, Union[int, str]]]:
        raise NotImplementedError("Options method must be implemented in subclass")

    def to_dict(
        self, *, include_options: bool = False, objects: QuerySet = None
    ) -> Dict[str, Union[str, List[Dict[str, Union[int, str]]]]]:
        result = {
            "id": self.id,
            "key": self.key,
            "title": self.title,
            "type": self.type,
        }

        if include_options:
            result["options"] = self.options(objects)

        return result

    def transform(self, value):
        if transform := self.queryset_transformation:
            return transform(value)

        return value
