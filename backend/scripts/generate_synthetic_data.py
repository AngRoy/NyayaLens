"""Generate the deterministic synthetic placement dataset for demos.

Usage:
    python backend/scripts/generate_synthetic_data.py --seed 42
    python backend/scripts/generate_synthetic_data.py --out shared/sample_data/placement_synthetic.csv

Produces a CSV that matches the schema in design-doc Appendix A and seeds
a 3:1 placement disparity between Male and Female so the headline demo
beat lands on DIR ≈ 0.56 before reweighting and ≈ 0.84 after.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_OUT = (
    Path(__file__).resolve().parents[2] / "shared" / "sample_data" / "placement_synthetic.csv"
)

BRANCHES = ["CSE", "ECE", "ME", "CE", "EE"]
CATEGORIES = ["General", "OBC", "SC", "ST"]
COMPANIES_HIGH = ["Google", "Microsoft", "Amazon", "Meta"]
COMPANIES_MID = ["TCS", "Infosys", "Wipro", "Capgemini", "Cognizant"]


def generate(n: int = 600, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    gender = rng.choice(["Male", "Female"], size=n, p=[0.65, 0.35])
    branch = rng.choice(BRANCHES, size=n, p=[0.30, 0.22, 0.18, 0.15, 0.15])
    category = rng.choice(CATEGORIES, size=n, p=[0.55, 0.20, 0.15, 0.10])

    base_cgpa = rng.normal(loc=7.5, scale=1.0, size=n).clip(4.0, 10.0)
    backlogs = rng.poisson(lam=0.3, size=n).clip(0, 6)
    internships = rng.poisson(lam=1.0, size=n).clip(0, 4)
    projects = rng.poisson(lam=2.0, size=n).clip(0, 8)

    male_names = ["Rahul", "Aakash", "Vikram", "Karan", "Rohan", "Arjun"]
    female_names = ["Priya", "Anjali", "Neha", "Pooja", "Kavya", "Riya"]
    last_names = ["Sharma", "Patel", "Singh", "Gupta", "Reddy", "Kumar", "Nair"]

    def name_for(g: str) -> str:
        first = rng.choice(male_names if g == "Male" else female_names)
        last = rng.choice(last_names)
        return f"{first} {last}"

    names = [name_for(g) for g in gender]
    roll_nos = [f"21{rng.choice(['CS', 'EC', 'ME', 'CE', 'EE'])}{i:03d}" for i in range(1, n + 1)]
    emails = [f"student{i:03d}@college.edu" for i in range(1, n + 1)]

    base_p = np.where(gender == "Male", 0.85, 0.50)
    p = base_p + 0.03 * (base_cgpa - 7.5) + 0.04 * (internships - 1.0) - 0.05 * backlogs
    p = p.clip(0.05, 0.97)
    placed = (rng.uniform(0.0, 1.0, size=n) < p).astype(int)

    score = np.where(
        placed == 1,
        rng.uniform(0.55, 0.95, size=n),
        rng.uniform(0.05, 0.55, size=n),
    )

    company: list[str] = []
    package: list[float] = []
    for is_placed, b, cg in zip(placed, branch, base_cgpa, strict=True):
        if not is_placed:
            company.append("")
            package.append(0.0)
            continue
        if cg > 8.5 and b in ("CSE", "ECE"):
            company.append(str(rng.choice(COMPANIES_HIGH)))
            package.append(round(float(rng.uniform(18.0, 32.0)), 2))
        else:
            company.append(str(rng.choice(COMPANIES_MID)))
            package.append(round(float(rng.uniform(3.5, 12.0)), 2))

    return pd.DataFrame(
        {
            "Roll_No": roll_nos,
            "Name": names,
            "Email": emails,
            "Gender": gender,
            "Branch": branch,
            "Category": category,
            "CGPA": np.round(base_cgpa, 2),
            "Backlogs": backlogs,
            "Internships": internships,
            "Projects": projects,
            "Score": np.round(score, 4),
            "Placed": placed,
            "Company": company,
            "Package_LPA": package,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate seeded placement CSV.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rows", type=int, default=600)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    df = generate(n=args.rows, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)

    by_gender = (
        df.groupby("Gender")["Placed"]
        .agg(["sum", "count", "mean"])
        .rename(columns={"sum": "placed", "count": "n", "mean": "rate"})
    )
    print(f"Wrote {len(df)} rows -> {args.out}")
    print(by_gender.to_string())
    rates = by_gender["rate"].to_dict()
    if "Male" in rates and "Female" in rates and rates["Male"] > 0:
        print(f"DIR (F/M) = {rates['Female'] / rates['Male']:.3f}")


if __name__ == "__main__":
    main()
