from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from typing import Optional

import requests

API_BASE = "https://api.linkedin.com/rest"


class LinkedInError(RuntimeError):
    pass


@dataclass
class LinkedInClient:
    access_token: str
    author_urn: str
    version: str
    timeout: int = 45

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "LinkedIn-Version": self.version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

    def _raise(self, response: requests.Response, action: str) -> None:
        if response.ok:
            return
        body = response.text[:1500]
        raise LinkedInError(
            f"LinkedIn {action} failed ({response.status_code}): {body}"
        )

    def upload_image_from_url(self, image_url: str) -> str:
        """Download an image and upload it to LinkedIn. Returns an image URN."""
        source = requests.get(image_url, timeout=self.timeout)
        source.raise_for_status()

        content_type = source.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if not content_type.startswith("image/"):
            guessed = mimetypes.guess_type(image_url)[0]
            content_type = guessed or "application/octet-stream"
        if not content_type.startswith("image/"):
            raise LinkedInError(f"image_url did not return an image: {content_type}")

        init = requests.post(
            f"{API_BASE}/images?action=initializeUpload",
            headers=self.headers,
            json={"initializeUploadRequest": {"owner": self.author_urn}},
            timeout=self.timeout,
        )
        self._raise(init, "image initialization")

        value = init.json().get("value") or {}
        upload_url = value.get("uploadUrl")
        image_urn = value.get("image")
        if not upload_url or not image_urn:
            raise LinkedInError("LinkedIn did not return an upload URL and image URN.")

        uploaded = requests.put(
            upload_url,
            data=source.content,
            headers={"Content-Type": content_type},
            timeout=self.timeout,
        )
        self._raise(uploaded, "image upload")
        return image_urn

    def create_post(
        self,
        caption: str,
        image_urn: Optional[str] = None,
        image_alt: str = "",
    ) -> str:
        payload: dict = {
            "author": self.author_urn,
            "commentary": caption,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        if image_urn:
            media = {"id": image_urn}
            if image_alt:
                media["title"] = image_alt[:200]
            payload["content"] = {"media": media}

        response = requests.post(
            f"{API_BASE}/posts",
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        self._raise(response, "post creation")

        post_id = (
            response.headers.get("x-restli-id")
            or response.headers.get("X-RestLi-Id")
        )
        if not post_id:
            post_id = "published-without-returned-id"
        return post_id
