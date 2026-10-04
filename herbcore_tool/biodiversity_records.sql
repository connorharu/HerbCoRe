USE new_herbarium;

DROP TABLE IF EXISTS biodiversity_records;

CREATE TABLE biodiversity_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barcode TEXT,
    collectioncode TEXT,
    catalognumber TEXT,
    scientificname TEXT,
    kingdom TEXT,
    family TEXT,
    genus TEXT,
    yearcollected TEXT,
    monthcollected TEXT,
    daycollected TEXT,
    country TEXT,
    stateprovince TEXT,
    county TEXT,
    locality TEXT,
    institutioncode TEXT,
    phylum TEXT,
    basisofrecord TEXT,
    verbatimlatitude TEXT,
    verbatimlongitude TEXT,
    identifiedby TEXT,
    collectionid INT,
    specificepithet TEXT,
    recordedby TEXT,
    decimallongitude TEXT,
    decimallatitude TEXT,
    modified TEXT,
    scientificnameauthorship TEXT,
    recordnumber TEXT,
	occurrenceremarks TEXT
);

ALTER TABLE biodiversity_records AUTO_INCREMENT = 1;

SELECT COUNT(*) FROM biodiversity_records;
SELECT * FROM biodiversity_records;
