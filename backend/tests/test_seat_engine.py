from app.services.seat_engine import find_violations, is_eight_adjacent, manhattan, place_candidates, plan_to_dict, SeatAssign

def test_manhattan():
    assert manhattan((0, 0), (2, 1)) == 3

def test_eight_adjacent_includes_diagonals():
    assert is_eight_adjacent((0, 0), (1, 1))          # 对角
    assert is_eight_adjacent((0, 0), (0, 1))          # 正邻
    assert not is_eight_adjacent((0, 0), (0, 2))      # 列差 2
    assert not is_eight_adjacent((0, 0), (2, 1))      # 行差 2
    assert not is_eight_adjacent((1, 1), (1, 1))      # 同位不算邻

def test_min_distance_placement():
    cands = [{"id": i, "name": f"C{i}", "ticket_no": f"T{i}", "paper_id": 1 + (i % 2)} for i in range(4)]
    assigns, unplaced = place_candidates(4, 4, 2, cands)
    assert len(assigns) + len(unplaced) == 4
    for i, a in enumerate(assigns):
        for b in assigns[i+1:]:
            assert manhattan((a.row, a.col), (b.row, b.col)) >= 2

def test_same_paper_not_adjacent_in_result():
    cands = [
        {"id": 1, "name": "A", "ticket_no": "T1", "paper_id": 1},
        {"id": 2, "name": "B", "ticket_no": "T2", "paper_id": 1},
        {"id": 3, "name": "C", "ticket_no": "T3", "paper_id": 2},
    ]
    assigns, _ = place_candidates(3, 3, 1, cands)
    viols = find_violations(3, 3, 1, assigns)
    assert not any(v.kind == "same_paper_adjacent" for v in viols)

def test_diagonal_same_paper_forces_unplaced():
    # 2x2 内两名同套：对角是唯一的“旧四邻可坐”位，八邻口径下也禁 → 只能坐一人。
    cands = [
        {"id": 1, "name": "A", "ticket_no": "T1", "paper_id": 1},
        {"id": 2, "name": "B", "ticket_no": "T2", "paper_id": 1},
    ]
    assigns, unplaced = place_candidates(2, 2, 1, cands)
    assert len(assigns) == 1
    assert len(unplaced) == 1

def test_diagonal_pair_detected_even_when_distance_ok():
    # 对角距离 = 2 满足最小曼哈顿，但同套八邻仍须判违规（只满足距离一条仍算失败）。
    assigns = [
        SeatAssign(1, "A", "T1", 1, 0, 0),
        SeatAssign(2, "B", "T2", 1, 1, 1),
    ]
    viols = find_violations(2, 2, 2, assigns)
    kinds = [v.kind for v in viols]
    assert kinds == ["same_paper_adjacent"]      # 距离达标不报距离；八邻只此一句

def test_distance_violation_even_when_papers_differ():
    # 不同套不存在八邻约束，但曼哈顿不达标仍须判违规（只满足八邻/非邻接一条仍算失败）。
    assigns = [
        SeatAssign(1, "A", "T1", 1, 0, 0),
        SeatAssign(2, "B", "T2", 2, 0, 1),
    ]
    viols = find_violations(2, 2, 2, assigns)
    assert [v.kind for v in viols] == ["distance"]

def test_eight_neighbor_emits_single_record():
    # 正邻同套：只能有一条同套相邻记录，禁止四邻/八邻两条并挂。
    assigns = [
        SeatAssign(1, "A", "T1", 1, 0, 0),
        SeatAssign(2, "B", "T2", 1, 0, 1),
    ]
    viols = find_violations(2, 2, 1, assigns)
    same = [v for v in viols if v.kind == "same_paper_adjacent"]
    assert len(same) == 1

def test_violation_detection():
    assigns = [
        SeatAssign(1, "A", "T1", 1, 0, 0),
        SeatAssign(2, "B", "T2", 1, 0, 1),
    ]
    viols = find_violations(2, 2, 2, assigns)
    kinds = {v.kind for v in viols}
    assert "distance" in kinds
    assert "same_paper_adjacent" in kinds

def test_stats_count_matches_violation_list():
    assigns = [
        SeatAssign(1, "A", "T1", 1, 0, 0),
        SeatAssign(2, "B", "T2", 1, 1, 1),
        SeatAssign(3, "C", "T3", 2, 0, 1),
    ]
    viols = find_violations(2, 2, 2, assigns)
    result = plan_to_dict(assigns, [], viols, 2, 2)
    assert result["stats"]["violations"] == len(result["violations"]) == len(viols)

def test_seed_layout_has_no_same_paper_eight_neighbor():
    # 复刻 seed：5x6、min_manhattan=2、12 人按 3 套循环。同套对角/正邻均不得同图并存。
    cands = [{"id": i + 1, "name": f"N{i}", "ticket_no": f"T{2026001+i}", "paper_id": 1 + (i % 3)}
             for i in range(12)]
    assigns, unplaced = place_candidates(5, 6, 2, cands)
    viols = find_violations(5, 6, 2, assigns)
    assert not unplaced
    assert not any(v.kind == "same_paper_adjacent" for v in viols)
    for i, a in enumerate(assigns):
        for b in assigns[i + 1:]:
            if a.paper_id == b.paper_id:
                assert not is_eight_adjacent((a.row, a.col), (b.row, b.col))
