"""BDD steps for task_management.feature — all step functions are sync (TestClient)."""
from pytest_bdd import scenarios, given, when, then, parsers

scenarios("../features/task_management.feature")


# ── Scenario: Create a new board ─────────────────────────────────────────────

@given("I am an authenticated user", target_fixture="scenario_headers")
def authenticated_user(headers):
    return headers


@when(parsers.parse('I create a board named "{board_name}"'), target_fixture="created_board")
def create_board(client, scenario_headers, board_name):
    r = client.post(
        "/api/boards",
        json={"name": board_name, "description": "BDD test board"},
        headers=scenario_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


@then("the board should be created successfully")
def verify_board_created(client, scenario_headers, created_board):
    r = client.get(f"/api/boards/{created_board['id']}", headers=scenario_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == created_board["name"]


@then("an audit log entry should be created")
def verify_audit_log(client, scenario_headers, created_board):
    r = client.get(
        f"/api/boards/{created_board['id']}/activity", headers=scenario_headers
    )
    assert r.status_code == 200
    assert len(r.json()) >= 1, f"Expected at least one activity entry, got: {r.json()}"


# ── Scenario: Add a card to a list ───────────────────────────────────────────

@given('I have a board with a "To Do" list', target_fixture="todo_list")
def board_with_todo_list(client, headers):
    br = client.post(
        "/api/boards",
        json={"name": "Card Test Board", "description": ""},
        headers=headers,
    )
    assert br.status_code == 201
    board_id = br.json()["id"]

    lr = client.post(
        f"/api/boards/{board_id}/lists",
        json={"name": "To Do", "position": 0},
        headers=headers,
    )
    assert lr.status_code == 201
    return lr.json()


@when(
    parsers.parse('I add a card titled "{card_title}" to the list'),
    target_fixture="created_card",
)
def add_card(client, headers, todo_list, card_title):
    r = client.post(
        f"/api/lists/{todo_list['id']}/cards",
        json={"title": card_title, "description": "", "position": 0},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


@then("the card should appear in the list")
def card_in_list(client, headers, todo_list, created_card):
    # Cards are fetched via the board-level endpoint (no direct list/cards route)
    board_id = todo_list["board_id"]
    r = client.get(f"/api/boards/{board_id}/cards", headers=headers)
    assert r.status_code == 200
    cards_in_list = [c for c in r.json() if c["list_id"] == todo_list["id"]]
    ids = [c["id"] for c in cards_in_list]
    assert str(created_card["id"]) in ids


@then("the card should have a unique position")
def card_unique_position(created_card):
    assert created_card["position"] is not None


# ── Scenario: Move card between lists ────────────────────────────────────────

@given('I have a card in the "To Do" list', target_fixture="move_ctx")
def card_in_todo(client, headers):
    br = client.post(
        "/api/boards",
        json={"name": "Move Test Board", "description": ""},
        headers=headers,
    )
    assert br.status_code == 201, br.text
    board_id = br.json()["id"]

    todo_r = client.post(
        f"/api/boards/{board_id}/lists",
        json={"name": "To Do", "position": 0},
        headers=headers,
    )
    assert todo_r.status_code == 201, todo_r.text
    todo = todo_r.json()

    inprog_r = client.post(
        f"/api/boards/{board_id}/lists",
        json={"name": "In Progress", "position": 1},
        headers=headers,
    )
    assert inprog_r.status_code == 201, inprog_r.text
    inprog = inprog_r.json()

    card_r = client.post(
        f"/api/lists/{todo['id']}/cards",
        json={"title": "Moveable Card", "description": "", "position": 0},
        headers=headers,
    )
    assert card_r.status_code == 201, card_r.text
    card = card_r.json()

    return {"card": card, "todo": todo, "inprog": inprog, "board_id": board_id}


@when('I move the card to "In Progress" list')
def move_card(client, headers, move_ctx):
    card_id = move_ctx["card"]["id"]
    inprog_id = move_ctx["inprog"]["id"]
    r = client.put(
        f"/api/cards/{card_id}/move",
        json={"list_id": inprog_id, "position": 0},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    move_ctx["moved_card"] = r.json()


@then("the card should be in the new list")
def card_in_new_list(move_ctx):
    assert str(move_ctx["moved_card"]["list_id"]) == move_ctx["inprog"]["id"]


@then("the position should be updated")
def position_updated(move_ctx):
    assert move_ctx["moved_card"]["position"] == 0


@then("an activity log should be recorded")
def activity_recorded(client, headers, move_ctx):
    board_id = move_ctx["board_id"]
    r = client.get(f"/api/boards/{board_id}/activity", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) > 0
