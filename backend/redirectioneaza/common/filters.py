from collections.abc import Callable

from django.db.models import QuerySet


class QueryFilter:
    id: str | None = None
    key: str | None = None
    type: str | None = None

    title: str | None = None

    queryset_key: str | None = None
    queryset_transformation: Callable | None = None

    def options(self, objects: QuerySet | None = None) -> list[dict[str, int | str]]:
        if objects is None:
            return self.options_default()

        try:
            return self.options_with_objects(objects)
        except NotImplementedError:
            return self.options_default()

    def options_with_objects(self, objects: QuerySet) -> list[dict[str, int | str]]:
        raise NotImplementedError("Options method must be implemented in subclass")

    def options_default(self) -> list[dict[str, int | str]]:
        raise NotImplementedError("Options method must be implemented in subclass")

    def title_for_option(self, option_value: int | str) -> str:
        """
        Returns the title for a given option value.
        This method can be overridden in subclasses to provide custom titles.
        """
        try:
            return str(next(item for item in self.options_default() if item["value"] == option_value)["title"])
        except (NotImplementedError, StopIteration, KeyError):
            return str(option_value)

    def to_dict(
        self, *, include_options: bool = False, objects: QuerySet | None = None
    ) -> dict[str, str | list[dict[str, int | str]]]:
        result = {
            "id": self.id,
            "key": self.key,
            "title": self.title,
            "type": self.type,
        }

        if include_options:
            result["options"] = self.options(objects)

        return result

    def transform_to_qs_value(self, value):
        if transform := self.queryset_transformation:
            return transform(value)

        return value
