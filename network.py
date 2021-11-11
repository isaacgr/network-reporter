import speedtest
import logging

log = logging.getLogger(__name__)


def get_speed():
    log.info('Getting network speed')
    s = speedtest.Speedtest()
    s.get_best_server()
    s.download(threads=None)
    s.upload(threads=None)
    res = s.results.dict()
    download = res['download']
    upload = res['upload']
    ping = res['ping']
    ip = res['client']['ip']
    log.info('Got network speed. [%.2f Mbps Down, %.2f Mbps Up]' % (download/1000000, upload/1000000))
    return {
        "method": "set.network.speed",
        "data": {
            'download': download,
            'upload': upload,
            'ping': ping,
            'ip': ip
        }
    }

