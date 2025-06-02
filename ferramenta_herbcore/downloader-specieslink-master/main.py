import click
import datetime
import json
import pandas as pd
import re

import requests
import scrapy

from scrapy.crawler import CrawlerProcess
from scrapy.http import FormRequest
from scrapy.utils.project import get_project_settings


class SpeciesLink(scrapy.Spider):
    name = 'specieslink'
    base_url = 'https://specieslink.net/search/index'
    form_data = {
        'action': 'records',
        'graph_type': 'horizontalBar',
        'graph_sort': 'value',
        'from': '0',
        'recs_order_by': 'random_order',
        'dups_mode': 'collect_full_key',
        'coll_groups': '',
        'coll_networks': '',
    }

    def __init__(self, barcodes, urls):
        self.barcodes = barcodes
        self.urls = urls

    def start_requests(self):
        for i, barcode in enumerate(self.barcodes):
            print('%d-%d' % (i, len(self.barcodes)))
            self.form_data['barcode'] = barcode

            yield FormRequest(self.base_url,
                              formdata=self.form_data,
                              callback=self.parse)

    def parse(self, response):
        for url in response.xpath('//img/@src').extract():
            if 'https://storage.googleapis.com/cria-zoomify' in url:
                if url not in self.urls:
                    self.urls.append(url)


@click.command()
@click.option('--csv', required=True, help='caminho para o arquivo csv com barcode a se utilizar o crawler')
@click.option('--reino', type=str)  # nao implementei :(
@click.option('--filo', type=str)  # nao implementei :(
@click.option('--classe', type=str)  # nao implementei :(
@click.option('--ordem', type=str)  # nao implementei :(
@click.option('--familia', type=str)
@click.option('--genero', type=str)  # nao implementei :(
@click.option('--epitetoespecifico', type=str)  # nao implementei :(
@click.option('--epitetoinfraespecifico', type=str)  # nao implementei :(
@click.option('--images', is_flag=True)
@click.version_option('0.0.1', prog_name='downloader-specieslink')
def main(csv, reino, filo, classe, ordem, familia, genero, epitetoespecifico, epitetoinfraespecifico, images):
    df = pd.read_csv(csv, header=0, index_col=None)
    barcodes = df['barcode'].values

    process = CrawlerProcess(get_project_settings())
    urls = []
    process.crawl(SpeciesLink, urls=urls, barcodes=barcodes)
    process.start()

    save_urls(familia, images, urls)


def save_urls(familia, imagens, urls):
    df = pd.DataFrame({'urls': urls})
    df.to_csv(get_filename('csv', familia, imagens), quoting=2, sep=";")


def save_json(family, images, records):
    filename = get_filename('json', family, images)
    with open(filename, 'w') as file:
        json.dump(records, file)


def get_filename(extension, family, images):
    filename = 'request+family+%s' % family
    if images:
        filename = filename + '+images'
    current_date = datetime.datetime.strftime(datetime.datetime.now(), '%Y+%m+%d')
    filename = filename + '+%s.%s' % (current_date, extension)
    print('save %s' % filename)
    return filename


if __name__ == '__main__':
    main()
