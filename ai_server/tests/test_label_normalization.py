from app.routers.ai import _normalize_label_result


def test_label_result_uses_nutrient_based_name_when_name_is_missing():
    result = _normalize_label_result({
        "name": "",
        "nutrients": [
            {"ingredient": "비타민C", "amount": "1000", "unit": "mg"},
            {"ingredient": "아연", "amount": "8.5", "unit": "mg"},
        ],
    })

    assert result["name"] == "비타민C 외 1종 영양제"
    assert result["ingredients"] == ["비타민C 1000mg", "아연 8.5mg"]


def test_label_result_preserves_visible_product_name():
    result = _normalize_label_result({
        "name": "센트룸 실버",
        "nutrients": [{"ingredient": "비타민D", "amount": "10", "unit": "mcg"}],
    })

    assert result["name"] == "센트룸 실버"
