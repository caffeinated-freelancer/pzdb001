class UniqueIdAllocator:
    current_id = 10000
    id_table: dict[str, int] = {}

    @staticmethod
    def get_unique_id(full_name: str, phone_number: str) -> int:
        key = f'{full_name}_{phone_number}'
        if phone_number in UniqueIdAllocator.id_table:
            return UniqueIdAllocator.id_table[key]
        else:
            UniqueIdAllocator.current_id += 1
            UniqueIdAllocator.id_table[key] = UniqueIdAllocator.current_id
            return UniqueIdAllocator.current_id
