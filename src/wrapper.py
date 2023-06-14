import argparse
import os
import re
import pathlib
import aiohttp
import Bio.SeqIO.FastaIO


URL = "https://iupred3.elte.hu"


def parse_args():
    """Returns a namespace with parsed command-line arguments."""
    description = "Cli wrapper for IUPred3 web interface"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "file",
        type=str,
        help="input file with protein sequence in fasta format"
    )
    parser.add_argument(
        "--token",
        type=str,
        default=os.getenv("CSRF_TOKEN"),
        help="csrf token from iupred3 cookie.",
    )
    parser.add_argument(
        "--sessionid",
        type=str,
        default=os.getenv("SESSION_ID"),
        help="sessionid from iupred3 cookie.",
    )
    return parser.parse_args()


async def main(args):
    file = pathlib.Path(args.file)
    if not file.exists():
        raise Exception("No such file or directory")
    data = {
        "email": "",
        "accession": "",
        "inp_seq": "",
        "aln_file": "",
        "csrfmiddlewaretoken": args.token,
    }
    cookies = {"csrftoken": args.token, "sessionid": args.sessionid}
    headers = {
        "Accept": "application/json",
        "Connection": "keep-alive",
    }
    async with aiohttp.ClientSession(URL) as session:
        resps = []
        with open(file, "r") as f:
            for record in Bio.SeqIO.FastaIO.SimpleFastaParser(f):
                data["inp_seq"] = record[1]
                async with session.post(
                        "/plot",
                        data=data,
                        cookies=cookies,
                        headers=headers,
                ) as resp:
                    resps.append(await resp.text())

        json_id_re = re.compile(r'raw_json(%[A-Z0-9]+)"')

        json_ids = []
        for resp in resps:
            line = [line for line in resp.split("\n") if "raw_json" in line][
                0
            ].strip()
            match = json_id_re.search(line)
            if match is not None:
                json_ids.append(match[1])

        resps = []
        for id in json_ids:
            async with session.get(
                    f"/raw_json{id}",
                    headers=headers,
            ) as resp:
                resps.append(await resp.json())

        for resp in resps:
            disordered = []
            for d in resp.get("iupred2"):
                if d > 0.5:
                    disordered.append("D")
                else:
                    disordered.append("-")
            print(resp.get("sequence"))
            print("".join(disordered))
