import argparse

from webservices.sync import SyncConsumer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('public_key')
    parser.add_argument('private_key')
    parser.add_argument('name')
    parser.add_argument('--host', default='http://localhost:8000/')
    args = parser.parse_args()
    consumer = SyncConsumer(args.host, args.public_key, args.private_key)
    print(consumer.consume('/', {'name': args.name})['greeting'])

if __name__ == '__main__':
    main()
