# TODO

## Kamień 04 
Z 'investment_sync.py' Wydzielić ImageSyncService — ma najmniej coupling-u
Python
python_worker/services/image_sync.py

## Kamień 05 
Z 'investment_sync.py' Wydzielić DeveloperResolver
Python
python_worker/services/developer_resolver.py

## Kamień 06 
W 'investment_sync.py' Uprościć process_batch() używając _prepare_batch_identifiers() jako helper Nie robimy nowej klasy, ale czyszczenie flow.