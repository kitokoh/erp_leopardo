import pytest
import os
import shutil
import json
import sys
import sqlite3
import asyncio

from PIL import Image
import cv2

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.media_manager import operations, models
from app.db.init_schema import initialize_database
from app.db.connection import get_db_connection, initialize_engine_and_session
from app.db.cruds.users import users_crud
from core.config import CONFIG

@pytest.fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test module."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
def test_db():
    config = CONFIG
    config.data['database_path'] = 'test_media_manager.db'
    config.data['media_files_path'] = '/tmp/media_files_test'
    config.data['default_download_path'] = '/tmp/downloads_test'

    initialize_engine_and_session(config.data)
    initialize_database(config.data)

    os.makedirs(config.get('media_files_path'), exist_ok=True)
    os.makedirs(config.get('default_download_path'), exist_ok=True)

    yield config

    os.remove(config.get('database_path'))
    shutil.rmtree(config.get('media_files_path'))
    shutil.rmtree(config.get('default_download_path'))

@pytest.fixture(scope="function")
def db_session(test_db):
    session = next(get_db_connection())
    yield session
    session.close()

@pytest.fixture(scope="module")
def test_users(test_db):
    session = next(get_db_connection())
    user1_data = {'username': 'test_uploader_1', 'password_hash': 'password1', 'full_name': 'Test Uploader One', 'email': 'uploader1@test.com', 'role_id': 1}
    user2_data = {'username': 'test_uploader_2', 'password_hash': 'password2', 'full_name': 'Test Uploader Two', 'email': 'uploader2@test.com', 'role_id': 1}

    user1_id = users_crud.add_user(session, user1_data)
    user2_id = users_crud.add_user(session, user2_data)

    session.commit()

    yield user1_id, user2_id

    users_crud.delete_user(session, user1_id)
    users_crud.delete_user(session, user2_id)
    session.commit()
    session.close()


@pytest.fixture(scope="function")
def dummy_files():
    dummy_image_path = "dummy_image.png"
    img = Image.new('RGB', (60, 30), color = 'red')
    img.save(dummy_image_path)

    dummy_video_path = "dummy_video.mp4"
    open(dummy_video_path, 'w').close()

    yield dummy_image_path, dummy_video_path

    os.remove(dummy_image_path)
    os.remove(dummy_video_path)

def test_models_to_dict_from_dict():
    video_metadata = {"duration": "10:00", "resolution": "1080p"}
    video = models.VideoItem(id="v1", title="Video 1", description="Desc v1", filepath=os.path.join("v1.mp4"), tags=["tag1", "tag2"], thumbnail_path=".thumbnails/v1.jpg", metadata=video_metadata)
    video_dict = video.to_dict()
    assert video_dict['metadata'] == video_metadata
    reconstructed_video = models.MediaItem.from_dict(video_dict)
    assert video == reconstructed_video
    assert reconstructed_video.metadata == video_metadata

    video_dict_from_db_row = {
        'id': "v1db", 'title': "Video DB", 'description': "Desc DB", 'type': "video",
        'filepath': "v1db.mp4", 'tags': ["db", "test"],
        'thumbnail_path': ".thumbnails/v1db.jpg",
        'metadata_json': json.dumps(video_metadata)
    }
    reconstructed_from_db_row = models.MediaItem.from_dict(video_dict_from_db_row)
    assert isinstance(reconstructed_from_db_row, models.VideoItem)
    assert reconstructed_from_db_row.metadata == video_metadata

@pytest.mark.asyncio
async def test_add_media(test_db, db_session, test_users, dummy_files):
    user1_id, _ = test_users
    dummy_image_path, dummy_video_path = dummy_files

    sample_metadata = {"source": "test_camera", "quality": "high"}
    video_item_obj = await operations.add_video("Async Test Video", "A test video for DB.", dummy_video_path, uploader_user_id=user1_id, tags=["tutorial", "testing"], metadata=sample_metadata)

    assert isinstance(video_item_obj, models.VideoItem)
    assert video_item_obj.metadata.get("source") == "test_camera"

    image_metadata = {"user_caption": "A beautiful test image"}
    image_item_obj = await operations.add_image("Async Test Image", "A test image for DB.", dummy_image_path, uploader_user_id=user1_id, tags=["nature", "testing"], metadata=image_metadata)

    assert image_item_obj.metadata.get("user_caption") == "A beautiful test image"
    assert "width" in image_item_obj.metadata
    assert image_item_obj.metadata.get("format") == "PNG"

@pytest.mark.asyncio
async def test_list_media(test_db, db_session, test_users, dummy_files):
    user1_id, user2_id = test_users
    dummy_image_path, dummy_video_path = dummy_files

    v1 = await operations.add_video("Video Alpha", "Desc video alpha", dummy_video_path, uploader_user_id=user1_id, tags=["catX", "videoTag"])
    i1 = await operations.add_image("Image Beta", "Desc image beta", dummy_image_path, uploader_user_id=user2_id, tags=["catY", "imageTag"])

    all_items = operations.list_media()
    assert len(all_items) == 2

    item_v1_listed = next(i for i in all_items if i.id == v1.id)
    assert sorted(item_v1_listed.tags) == sorted(["catx", "videotag"])

@pytest.mark.asyncio
async def test_search_media(test_db, db_session, test_users, dummy_files):
    user1_id, _ = test_users
    dummy_image_path, dummy_video_path = dummy_files

    v_s1_u1 = await operations.add_video("Alpha Search User1", "Journey to alpha point.", dummy_video_path, uploader_user_id=user1_id, tags=["adventureS"])
    results = operations.search_media(query="Alpha Search User1")
    assert len(results) == 1
    assert results[0].id == v_s1_u1.id

@pytest.mark.asyncio
async def test_download_media(test_db, db_session, test_users, dummy_files):
    user1_id, _ = test_users
    dummy_image_path, dummy_video_path = dummy_files
    config = test_db

    v1 = await operations.add_video("Download Vid Async", "Vid to download", dummy_video_path, uploader_user_id=user1_id, tags=["download", "videoAsync"])
    l1 = operations.add_link("Download Link Async", "Link to save", "http://download-async.example.com", uploader_user_id=user1_id, tags=["download", "linkAsync"])

    media_ids_to_download = [v1.id, l1.id]
    downloaded_files = await operations.download_selected_media(media_ids_to_download, config.get('default_download_path'))

    assert len(downloaded_files) == 2
    links_file_path = os.path.join(config.get('default_download_path'), "downloaded_links.txt")
    assert links_file_path in downloaded_files
    with open(links_file_path, 'r') as f:
        content = f.read()
        assert "http://download-async.example.com" in content