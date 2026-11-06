from enumerating_methods.box_search_common import update_upper_bounds


def test_update_upper_bounds_keeps_only_maximal_bounds():
    assert update_upper_bounds([(10, 10)], (4, 6)) == [(4, 10), (10, 6)]
    bounds = update_upper_bounds([(4, 10), (10, 6)], (3, 5))
    assert bounds == [(3, 10), (10, 5)]


def test_point_on_boundary_does_not_split_unrelated_bound():
    assert update_upper_bounds([(4, 10)], (4, 2)) == [(4, 10)]
