import asyncio
import aiohttp
import json
import argparse
import logging
import sys
import random
import string
import signal
from base64 import b64encode
from network import get_speed

FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"
datefmt = "%Y-%m-%d-%H:%M:%S"

log = logging.getLogger(__name__)


def parse_commandline():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--url',
        required=True,
        metavar='URL',
        help='URL to post results to'
    )

    parser.add_argument(
        '--log',
        metavar='FILENAME',
        help='Logfile of client, if any'
    )

    return parser.parse_args()

def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def format_jsonrpc(result):
    """
    Format the result as a jsonrpc request
    """
    jsonrpc = {
        "jsonrpc": "2.0",
        "method": result['method'],
        "params": result['data'],
        "id": id_generator()
    }
    return jsonrpc

async def shutdown(signal, loop):
    """Cleanup tasks tied to the service's shutdown."""
    log.info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]

    [task.cancel() for task in tasks]

    log.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def run(url):
    while True:
        loop = asyncio.get_event_loop()
        network = await loop.run_in_executor(None, get_speed)

        data = json.dumps(format_jsonrpc(network))
        auth = b64encode(b'')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + auth.decode('utf-8')
        }

        async with aiohttp.ClientSession(headers=headers,connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(url, data=data) as response:
                log.info('Server response: Status [%s], Body [%s]' % (response.status, await response.text()))
        await asyncio.sleep(300)

def main():
    options = parse_commandline()

    logfile = options.log
    if not logfile:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                            format=FORMAT, datefmt=datefmt)
    else:
        logging.basicConfig(filename=logfile, level=logging.INFO,
                            format=FORMAT, datefmt=datefmt)

    loop = asyncio.get_event_loop()

    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop)))

    try:
        loop.create_task(run(options.url))
        loop.run_forever()
    finally:
        log.warning('Closing loop')
        loop.close()

if __name__ == '__main__':
    main()
