class DeserializationError(Exception):
    pass


class FieldMissingError(DeserializationError):
    def __init__(self, *fields: str):
        if not fields:
            msg = "missing a required field"
        else:
            msg = (f'{'Field' if len(fields) == 1 else 'Fields'} '
                   f'{", ".join(map(lambda f: f"\"{f}\"", fields))} '
                   f'{"is" if len(fields) == 1 else "are"} missing')

        super().__init__(msg)
