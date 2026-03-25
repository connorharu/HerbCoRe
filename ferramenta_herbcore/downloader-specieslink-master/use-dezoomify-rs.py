import os

import click
import pandas as pd


@click.command()
@click.option('--input', required=True)
@click.option('--output', required=True)
def main(input, output):

    df = pd.read_csv(input, sep=';', index_col=0)

    for i, (idx, row) in enumerate(df.iterrows()):
        print('%d-%d' % (i, df.shape[0]))
        url = row['urls']
        if 'https://storage.googleapis.com/cria-zoomify/' in url:
            url = url[0:url.index('/TileGroup0/')]
            image_code = url[url.rindex('/')+1:]
            url = url + '/ImageProperties.xml'
            print(url, image_code)

            os.makedirs(output, exist_ok=True)
            filename = os.path.join(output, image_code)
            if not os.path.exists(filename):
                os.system('dezoomify-rs.exe -H Referer: %s %s.jpg -l' % (url, filename))


if __name__ == "__main__":
    main()