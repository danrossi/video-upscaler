import argparse
import enum
from typing import Any, Callable, Iterable, Optional, Sequence, Tuple, TypeVar, Union

E = TypeVar("E", bound=enum.Enum)

__all__ = ["enum_action"]


def enum_action(enum_class: E):
    
    def enum_by_value_type(enum_class):
        def parse_enum_value(s):
            try:
                # Try to convert to integer and get enum by value
                val = int(s)
                return enum_class(val)
            except ValueError:
                # If not an integer, try to get enum by name (case-insensitive)
                try:
                    return enum_class[s.upper()]
                except KeyError:
                    raise argparse.ArgumentTypeError(
                        f"Invalid choice: '{s}'. Must be one of {list(enum_class.__members__.keys())} "
                        f"or their corresponding integer values."
                    )
        return parse_enum_value

    class EnumAction(argparse.Action):
        def __init__(
            self,
            option_strings: Sequence[str],
            dest: str,
            nargs: Optional[Union[int, str]] = None,
            const: Optional[E] = None,
            default: Union[E, str, None] = None,
            type: Optional[
                Union[
                    Callable[[str], E],
                    Callable[[str], E],
                    argparse.FileType,
                ]
            ] = None,
            choices: Optional[Iterable[E]] = None,
            required: bool = False,
            help: Optional[str] = None,
            metavar: Optional[Union[str, Tuple[str, ...]]] = None,
        ) -> None:
            #print(default)
            #if isinstance(default, str):
            #    default = enum_class[default.upper()]
            #help = f"(default: {default.value} ({default.name.lower()}))"
            help = f"(default: {default}"
            
            type = enum_by_value_type(enum_class)
            self.cls = enum_class
            super().__init__(
                option_strings,
                dest,
                nargs=nargs,
                const=const,
                default=default,
                type=type,
                choices=list(enum_class),
                #choices=[variant.value for variant in enum_class],
                #choices=[variant.name.lower() for variant in enum_class],  # type: ignore
                required=required,
                help=help,
                metavar=metavar,
            )

        def __call__(  # type: ignore
            self,
            parser: argparse.ArgumentParser,
            namespace: argparse.Namespace,
            values: Union[str, Sequence[Any], None] = None,
            option_string: Optional[str] = None,
        ) -> None:
            #if not isinstance(values, str):
            #    raise TypeError
            #converted_values = [enum_class(value) for value in values]
            #setattr(namespace, self.dest, getattr(self.cls, converted_values))
            setattr(namespace, self.dest, getattr(self.cls, values.name))

    return EnumAction