"""Importing this package registers every command.

Order matters only for the duplicate check in `Registry.add`, which will fail
loudly if two modules claim the same name. That is the intended behaviour: a
silent shadowing between the city and run command sets would be very hard to
notice and very easy to introduce.
"""

from . import city, core, run  # noqa: F401  (imported for side effects)

__all__ = ['city', 'core', 'run']
