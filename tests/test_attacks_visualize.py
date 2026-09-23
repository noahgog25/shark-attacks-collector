from pathlib import Path

import pandas as pd

from src.attacks_visualize import plot_attack_locations


def test_plot_attack_locations_cree_une_image(tmp_path: Path):
    input_path = tmp_path / "attacks.csv"
    output_path = tmp_path / "attack_locations.png"
    pd.DataFrame(
        {
            "latitude": [29.0, -34.0],
            "longitude": [-81.0, 18.0],
            "geocoded_query": ["Florida, USA", "South Africa"],
        }
    ).to_csv(input_path, index=False)

    result = plot_attack_locations(input_path, output_path)

    assert result == output_path
    assert output_path.exists()