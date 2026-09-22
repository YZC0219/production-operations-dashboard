from app import app

def test_anonymous_redirected_to_login():
    client=app.test_client()
    response=client.get("/",follow_redirects=False)
    assert response.status_code==302
    assert "/login" in response.headers["Location"]

def test_api_requires_login():
    response=app.test_client().get("/api/machines")
    assert response.status_code==401
    assert response.json["success"] is False

def test_admin_can_login():
    client=app.test_client()
    response=client.post("/login",data={"username":"admin","password":"Admin@123456"})
    assert response.status_code==302
    assert "/password" in client.get("/",follow_redirects=False).headers["Location"]

def authenticated_admin():
    client=app.test_client()
    client.post("/login",data={"username":"admin","password":"Admin@123456"})
    with client.session_transaction() as user_session:
        user_session["must_change_password"]=False
    return client

def test_admin_pages_and_services():
    client=authenticated_admin()
    for path in ["/","/master-data","/reports","/admin","/security"]:
        assert client.get(path).status_code==200
    assert client.get("/api/master-data").status_code==200
    assert client.get("/api/audit-logs").status_code==200
    assert client.get("/api/security-checks").status_code==200

def test_export_and_backup():
    client=authenticated_admin()
    assert client.get("/export/machines").status_code==200
    assert client.post("/api/backup").status_code==200

def test_viewer_cannot_open_admin_page():
    client=app.test_client()
    with client.session_transaction() as user_session:
        user_session.update(user_id=999,username="viewer",display_name="只读",role="viewer",must_change_password=False)
    assert client.get("/admin",follow_redirects=False).status_code==302
    assert client.get("/api/users").status_code==403
