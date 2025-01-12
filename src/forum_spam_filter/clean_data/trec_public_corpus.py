from concurrent.futures import ProcessPoolExecutor
from .spam_assassin import parse_email
from functools import partial
import urllib.request
from pathlib import Path, PurePath
import os.path
import pandas as pd
import tarfile
import hashlib
import logging
from .util import LABEL_MAP, chunk_greater_than_512
from typing import TypedDict
import multiprocessing as mp

LOG = logging.getLogger(__name__)

class _Resource(TypedDict):
    url: str
    referrer: str
    md5: str

_RESOURCES: list[_Resource] = [
    {
        "url": "https://plg.uwaterloo.ca/cgi-bin/cgiwrap/gvcormac/trec07p.tgz",
        "referrer": "https://plg.uwaterloo.ca/cgi-bin/cgiwrap/gvcormac/foo07",
        "md5": "59c3df3efeb2fbd23babc18136bd466a",
    },
    {
        "url": "https://plg.uwaterloo.ca/cgi-bin/cgiwrap/gvcormac/trec06p.tgz",
        "referrer": "https://plg.uwaterloo.ca/cgi-bin/cgiwrap/gvcormac/foo06",
        "md5": "882d5de429562adf9071c130ddbf0936",
    },
    {
        "url": "https://plg.uwaterloo.ca/cgi-bin/cgiwrap/gvcormac/trec05p-1.tgz",
        "referrer": "https://plg.uwaterloo.ca/cgi-bin/cgiwrap/gvcormac/foo",
        "md5": "1689e711c4bb293d83858716f32c61db",
    },
]

_DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets"

def _download_if_not_present(dest_dir = _DEFAULT_DATASET_PATH):
    for r in _RESOURCES:
        target = dest_dir / os.path.basename(r["url"])
        if target.exists() and hashlib.md5(target.read_bytes()).hexdigest() == r["md5"]:
            LOG.info(f"Skipping download of {r['url']} as it already exists at {target}")
        else:
            LOG.info(f"Downloading {r['url']} to {target}")
            req = urllib.request.Request(r["url"], headers={"Referer": r["referrer"]})
            with (
                    urllib.request.urlopen(req) as response,
                    target.open("wb") as target_file,
            ):
                target_file.write(response.read())

def _process_email_batch(tb: Path, batch: list[tuple[str, str]]) -> list[dict[str, str | int]]:
    res = []
    with tarfile.open(tb, mode="r:gz") as tar:
        for label, filename in batch:
            email_file = tar.extractfile(filename)
            assert email_file is not None, f"Could not extract {filename} from {tb}"
            body = parse_email(email_file)
            label_idx = LABEL_MAP[label]
            res.append({"text": body, "label": label_idx})
    return res

def _process_tarball(tb: Path) -> pd.DataFrame:
    with tarfile.open(tb, mode="r:gz") as tar:
        prefix = os.path.commonprefix(tar.getnames())
        prefix = prefix.rstrip("/")
        index_file_path = PurePath(f"{prefix}/full/index")
        index_file = tar.extractfile(index_file_path.as_posix())
        assert index_file is not None
        email_metadata: list[tuple[str, str]] = []
        for line in index_file.read().decode("utf-8").split("\n"):
            line_parts = line.strip().split(" ")
            if len(line_parts) == 1 and line_parts[0] == "":
                continue
            if len(line_parts) != 2:
                LOG.warning(f"Skipping line: \"{line}\" in {tb} because it does not have a space in it")
                continue
            label, filename = line_parts
            filename = filename.removeprefix("../data/")
            filename = f"{prefix}/data/{filename}"
            email_metadata.append((label, filename))
    with ProcessPoolExecutor() as exc:
        f = []
        fn = partial(_process_email_batch, tb)
        batch_size = (len(email_metadata) + mp.cpu_count() - 1) // mp.cpu_count()
        for i in range(0, len(email_metadata), batch_size):
            f.append(exc.submit(fn, email_metadata[i:i + batch_size]))
        return pd.concat([pd.DataFrame(res) for res in [future.result() for future in f]], ignore_index=True)

def load_trec_dataset(dest_dir: Path = _DEFAULT_DATASET_PATH) -> pd.DataFrame:
    _download_if_not_present(dest_dir)

    df = pd.DataFrame(columns=["text", "label"])

    tarballs = [dest_dir / os.path.basename(r["url"]) for r in _RESOURCES]
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as exc:
        parts = list(exc.map(_process_tarball, tarballs))
        df = pd.concat(parts, ignore_index=True)

    # Post-processing
    # Remove any rows with empty text
    df["text"] = df["text"].map(lambda x: x.strip())
    df = df[df["text"].map(len) > 0]

    # Save the processed dataset
    df.to_csv(dest_dir / "trec_public_corpus.csv", index=False)

    # Split text into chunks of 512 tokens
    df["text_chunks"] = df["text"].apply(chunk_greater_than_512)
    df = df.explode("text_chunks", ignore_index=True)
    df = df.drop(columns=["text"])
    df = df.rename(columns={"text_chunks": "text"})

    return df
