# downloader-specieslink

### 1- Baixe o json e csv (com as urls das imagens)
#### 1.1- Substitua Piperaceae pela família desejada
```
    $ pip install -r requirements.txt
    $ python main.py --familia=Piperaceae --images
```


### 2- Use o dezoomify para baixar as imagens 
#### 2.1- Instale o libssl
````
    $ wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_amd64.deb
    $ sudo dpkg -i libssl1.1_1.1.0g-2ubuntu4_amd64.deb
    $ wget https://github.com/lovasoa/dezoomify-rs/releases/download/v2.11.2/dezoomify-rs-linux.tgz 
````

#### 2.2- Rode use-dezoomify-rs.py
#### 2.2.1- urls.csv é o arquivo gerado na etapa 1
```
    $ python use-dezoomify-rs.py --input=urls.csv --ouput=a
```



