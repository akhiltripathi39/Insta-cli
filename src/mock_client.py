import os
import json
import random
from datetime import datetime, timedelta, timezone
from typing import List, Any

class MockUser:
    def __init__(self, pk: str, username: str, full_name: str, biography: str = "", 
                 follower_count: int = 0, following_count: int = 0, media_count: int = 0,
                 profile_pic_url: str = ""):
        self.pk = pk
        self.username = username
        self.full_name = full_name
        self.biography = biography
        self.follower_count = follower_count
        self.following_count = following_count
        self.media_count = media_count
        self.profile_pic_url = profile_pic_url or f"https://api.dicebear.com/7.x/adventurer/svg?seed={username}"

class MockMedia:
    def __init__(self, pk: str, id: str, code: str, user: MockUser, caption_text: str,
                 like_count: int = 0, comment_count: int = 0, media_type: int = 1,
                 taken_at: datetime = None, has_liked: bool = False):
        self.pk = pk
        self.id = id
        self.code = code
        self.user = user
        self.caption_text = caption_text
        self.like_count = like_count
        self.comment_count = comment_count
        self.media_type = media_type  # 1 = Photo, 2 = Video
        self.taken_at = taken_at or (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48)))
        self.has_liked = has_liked
        self.thumbnail_url = f"https://picsum.photos/seed/{code}/150/150"

class MockDirectMessage:
    def __init__(self, id: str, user_id: str, text: str, timestamp: datetime,
                 clip: MockMedia = None, media_share: MockMedia = None, media: MockMedia = None, visual_media: Any = None, item_type: str = None):
        self.id = id
        self.user_id = user_id
        self.text = text
        self.timestamp = timestamp
        self.clip = clip
        self.media_share = media_share
        self.media = media
        self.visual_media = visual_media
        self.item_type = item_type or (
            "clip" if clip else (
                "media_share" if media_share else (
                    "media" if media else (
                        "visual_media" if visual_media else "text"
                    )
                )
            )
        )

class MockDirectThread:
    def __init__(self, id: str, users: List[MockUser], messages: List[MockDirectMessage], 
                 thread_type: str = "private", thread_title: str = ""):
        self.id = id
        self.users = users
        self.messages = sorted(messages, key=lambda m: m.timestamp, reverse=True)
        self.thread_type = thread_type
        self.thread_title = thread_title or (users[0].username if users else "Direct Chat")

class MockClient:
    """A mock implementation of instagrapi.Client for offline testing."""
    
    def __init__(self):
        self.user_id = "10001"
        self.username = "mock_user"
        self.is_logged_in = False
        self.challenge_code_handler = None
        self.change_password_handler = None
        self.settings = {}

        # Prepopulate Mock Database
        self._users = {
            "10001": MockUser("10001", "mock_user", "Mock User (You)", "Testing out the cool Instagram CLI", 42, 128, 5),
            "20001": MockUser("20001", "nasa", "NASA", "Explore the universe and discover our home planet.", 88000000, 102, 3842),
            "20002": MockUser("20002", "programmer_humor", "Programmer Humor", "The official source of coding laughter.", 124000, 12, 452),
            "20003": MockUser("20003", "nature_pics", "Nature Pictures", "Daily dose of green. DM to feature.", 45000, 200, 1105),
            "20004": MockUser("20004", "antigravity_ai", "Antigravity AI", "Google DeepMind's premier CLI building assistant.", 100000, 1, 100),
            "20005": MockUser("20005", "alice", "Alice Cooper", "Coffee enthusiast and code decorator.", 320, 420, 12),
            "20006": MockUser("20006", "bob", "Bob Builder", "Can we build it? Yes, we can CLI!", 99, 100, 3)
        }

        # Media Database
        self._medias = [
            MockMedia(
                pk="media_nasa_1", id="media_nasa_1_id", code="CtNASA1",
                user=self._users["20001"],
                caption_text="Hubble's stunning view of the Eagle Nebula, showcasing the Pillars of Creation in unprecedented detail.",
                like_count=45293, comment_count=382,
                taken_at=datetime.now(timezone.utc) - timedelta(hours=3)
            ),
            MockMedia(
                pk="media_prog_1", id="media_prog_1_id", code="CtPROG1",
                user=self._users["20002"],
                caption_text="There are 10 types of people in the world: those who understand binary, and those who don't. #coding #programmer #humor",
                like_count=8202, comment_count=112,
                taken_at=datetime.now(timezone.utc) - timedelta(hours=8)
            ),
            MockMedia(
                pk="media_nature_1", id="media_nature_1_id", code="CtNAT1",
                user=self._users["20003"],
                caption_text="A serene morning at Lake Moraine in Alberta, Canada. The water is a perfect turquoise. #nature #mountains",
                like_count=3120, comment_count=45,
                taken_at=datetime.now(timezone.utc) - timedelta(days=1)
            ),
            MockMedia(
                pk="media_anti_1", id="media_anti_1_id", code="CtANTI1",
                user=self._users["20004"],
                caption_text="We just launched the ultimate Instagram CLI tool in your terminal! Check it out! #cli #tui #antigravity #python",
                like_count=999, comment_count=99,
                taken_at=datetime.now(timezone.utc) - timedelta(days=2)
            )
        ]

        # DM Database
        now = datetime.now(timezone.utc)
        self._threads = {
            "thread_alice": MockDirectThread(
                id="thread_alice",
                users=[self._users["20005"]],
                messages=[
                    MockDirectMessage("m1", "20005", "Hey! Are you working on the Instagram CLI?", now - timedelta(hours=5)),
                    MockDirectMessage("m2", "10001", "Yes, building it right now in python!", now - timedelta(hours=4, minutes=58)),
                    MockDirectMessage("m3", "20005", "Awesome. Does it support DMs?", now - timedelta(hours=4, minutes=57)),
                    MockDirectMessage("m4", "10001", "Absolutely, you are reading this through it!", now - timedelta(hours=4, minutes=56)),
                    MockDirectMessage("m5", "20005", "Whoa! That is super cool! Let's get coffee later.", now - timedelta(hours=1)),
                    MockDirectMessage("m6", "20005", "", now - timedelta(minutes=10),
                                      clip=MockMedia(
                                          pk="media_nasa_1", id="media_nasa_1_id", code="CtNASA1",
                                          user=MockUser("20001", "nasa", "NASA", "Explore...", 88000000, 102, 3842),
                                          caption_text="Hubble's view of Eagle Nebula",
                                          like_count=45293, comment_count=382, media_type=2
                                      )),
                    MockDirectMessage("m7", "20005", "", now - timedelta(minutes=2),
                                      media=MockMedia(
                                          pk="media_alice_photo_1", id="media_alice_photo_1_id", code="AlicePhoto1",
                                          user=self._users["20005"],
                                          caption_text="",
                                          like_count=0, comment_count=0, media_type=1
                                      ))
                ]
            ),
            "thread_bob": MockDirectThread(
                id="thread_bob",
                users=[self._users["20006"]],
                messages=[
                    MockDirectMessage("b1", "20006", "Can we build it?", now - timedelta(days=1)),
                    MockDirectMessage("b2", "10001", "Yes we can! The terminal CLI is running smoothly.", now - timedelta(hours=22)),
                    MockDirectMessage("b3", "20006", "Great job, bro!", now - timedelta(hours=21))
                ]
            )
        }

    def load_settings(self, path: str):
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.settings = json.load(f)
            self.is_logged_in = self.settings.get("is_logged_in", False)
            self.username = self.settings.get("username", "mock_user")
            self.user_id = self.settings.get("user_id", "10001")
            return True
        return False

    def dump_settings(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.settings = {
            "is_logged_in": self.is_logged_in,
            "username": self.username,
            "user_id": self.user_id
        }
        with open(path, 'w') as f:
            json.dump(self.settings, f, indent=4)
        return True

    def login(self, username: str, password: str, verification_code: str = "") -> bool:
        if username == "fail_login":
            raise Exception("Mock Login Failed: Invalid Credentials")
        elif username == "2fa_user" and not verification_code:
            from instagrapi.exceptions import TwoFactorRequired
            raise TwoFactorRequired("2FA Code Required")
        elif username == "challenge_user" and self.challenge_code_handler:
            # Trigger challenge choice
            from instagrapi.mixins.challenge import ChallengeChoice
            code = self.challenge_code_handler(username, ChallengeChoice.SMS)
            if code != "123456":
                raise Exception("Mock Challenge Failed: Invalid verification code")
        
        self.username = username
        self.is_logged_in = True
        return True

    def two_factor_login(self, code: str) -> bool:
        if code == "123456" or code:
            self.is_logged_in = True
            return True
        raise Exception("Invalid 2FA code")

    def logout(self) -> bool:
        self.is_logged_in = False
        return True

    def get_timeline_feed(self) -> List[MockMedia]:
        if not self.is_logged_in:
            raise Exception("Please login first")
        return self._medias

    def user_info_by_username(self, username: str) -> MockUser:
        if not self.is_logged_in:
            raise Exception("Please login first")
        
        # Search locally
        for u in self._users.values():
            if u.username == username:
                return u
        
        # If not found, return a dynamic mock user
        new_user = MockUser(
            pk=str(random.randint(30000, 99999)),
            username=username,
            full_name=f"{username.title()} Mock",
            biography=f"This is a generated mock profile for @{username}.",
            follower_count=random.randint(100, 10000),
            following_count=random.randint(50, 1000),
            media_count=random.randint(5, 50)
        )
        self._users[new_user.pk] = new_user
        return new_user

    def user_medias(self, user_id: str, amount: int = 20) -> List[MockMedia]:
        if not self.is_logged_in:
            raise Exception("Please login first")
        
        user = self._users.get(user_id)
        if not user:
            return []
            
        # Return a couple of mock posts for this specific user
        user_posts = [m for m in self._medias if m.user.pk == user_id]
        if not user_posts:
            # Generate temporary posts
            for i in range(3):
                post = MockMedia(
                    pk=f"media_{user.username}_{i}",
                    id=f"media_{user.username}_{i}_id",
                    code=f"Ct{user.username.upper()[:3]}{i}",
                    user=user,
                    caption_text=f"Beautiful day in the life of @{user.username}! Post #{i+1} #mock #cli",
                    like_count=random.randint(10, 500),
                    comment_count=random.randint(1, 50),
                    taken_at=datetime.now(timezone.utc) - timedelta(days=i+1)
                )
                self._medias.append(post)
                user_posts.append(post)
        return user_posts[:amount]

    def direct_threads(self, amount: int = 20) -> List[MockDirectThread]:
        if not self.is_logged_in:
            raise Exception("Please login first")
        return list(self._threads.values())[:amount]

    def direct_thread(self, thread_id: str, amount: int = 20) -> MockDirectThread:
        if not self.is_logged_in:
            raise Exception("Please login first")
        thread = self._threads.get(thread_id)
        if not thread:
            # Maybe search by username
            for t in self._threads.values():
                if t.users[0].username == thread_id:
                    return t
            raise Exception("Thread not found")
        return thread

    def direct_send(self, text: str, thread_ids: List[str] = None, recipient_users: List[str] = None) -> MockDirectMessage:
        if not self.is_logged_in:
            raise Exception("Please login first")
        
        msg = MockDirectMessage(
            id=f"msg_{random.randint(1000, 9999)}",
            user_id="10001",
            text=text,
            timestamp=datetime.now(timezone.utc)
        )

        if thread_ids:
            for tid in thread_ids:
                if tid in self._threads:
                    self._threads[tid].messages.insert(0, msg)
        elif recipient_users:
            # Send by username or user ID
            username = recipient_users[0]
            # Find user
            recipient = None
            for u in self._users.values():
                if u.username == username or u.pk == username:
                    recipient = u
                    break
            if not recipient:
                recipient = self.user_info_by_username(username)
            
            # Find or create thread
            thread_id = f"thread_{recipient.username}"
            if thread_id in self._threads:
                self._threads[thread_id].messages.insert(0, msg)
            else:
                self._threads[thread_id] = MockDirectThread(
                    id=thread_id,
                    users=[recipient],
                    messages=[msg]
                )
        return msg

    def media_like(self, media_id: str) -> bool:
        if not self.is_logged_in:
            raise Exception("Please login first")
        
        for m in self._medias:
            if m.id == media_id or m.pk == media_id:
                if not m.has_liked:
                    m.like_count += 1
                    m.has_liked = True
                return True
        return False

    def media_comment(self, media_id: str, text: str) -> Any:
        if not self.is_logged_in:
            raise Exception("Please login first")
        
        for m in self._medias:
            if m.id == media_id or m.pk == media_id:
                m.comment_count += 1
                # Return dummy comment object
                class Comment:
                    def __init__(self, text_val: str):
                        self.pk = f"comment_{random.randint(1000, 9999)}"
                        self.text = text_val
                return Comment(text)
        raise Exception("Media not found")

    def photo_upload(self, path: str, caption: str) -> MockMedia:
        if not self.is_logged_in:
            raise Exception("Please login first")
        
        if not os.path.exists(path) and path != "mock_path.jpg":
            raise Exception(f"File not found: {path}")
            
        new_media = MockMedia(
            pk=f"media_upload_{random.randint(1000, 9999)}",
            id=f"media_upload_{random.randint(1000, 9999)}_id",
            code="CtUPLOAD",
            user=self._users["10001"],
            caption_text=caption,
            like_count=0,
            comment_count=0,
            taken_at=datetime.now(timezone.utc)
        )
        self._medias.insert(0, new_media)
        # Increment our media count
        self._users["10001"].media_count += 1
        return new_media

    def username_from_user_id(self, user_id: str) -> str:
        user_id = str(user_id)
        if user_id in self._users:
            return self._users[user_id].username
        raise Exception("User not found")
