from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path
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
    timeout: int = 60

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
        raise LinkedInError(f"LinkedIn {action} failed ({response.status_code}): {response.text[:1500]}")

    def upload_image_from_url(self, image_url: str) -> str:
        source = requests.get(image_url, timeout=self.timeout)
        source.raise_for_status()
        content_type = source.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if not content_type.startswith("image/"):
            content_type = mimetypes.guess_type(image_url)[0] or "application/octet-stream"
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
        upload_url, image_urn = value.get("uploadUrl"), value.get("image")
        if not upload_url or not image_urn:
            raise LinkedInError("LinkedIn did not return an upload URL and image URN.")

        uploaded = requests.put(upload_url, data=source.content, headers={"Content-Type": content_type}, timeout=self.timeout)
        self._raise(uploaded, "image upload")
        return image_urn

    def upload_document(self, file_path: Path) -> str:
        file_path = Path(file_path)
        if not file_path.exists():
            raise LinkedInError(f"Document file does not exist: {file_path}")

        init = requests.post(
            f"{API_BASE}/documents?action=initializeUpload",
            headers=self.headers,
            json={"initializeUploadRequest": {"owner": self.author_urn}},
            timeout=self.timeout,
        )
        self._raise(init, "document initialization")
        value = init.json().get("value") or {}
        upload_url, document_urn = value.get("uploadUrl"), value.get("document")
        if not upload_url or not document_urn:
            raise LinkedInError("LinkedIn did not return an upload URL and document URN.")

        with file_path.open("rb") as handle:
            uploaded = requests.put(
                upload_url,
                data=handle,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": mimetypes.guess_type(file_path.name)[0] or "application/pdf",
                },
                timeout=120,
            )
        self._raise(uploaded, "document upload")
        return document_urn

    def create_post(self, caption: str, image_urn: Optional[str] = None, image_alt: str = "", document_urn: Optional[str] = None, document_title: str = "") -> str:
        if image_urn and document_urn:
            raise LinkedInError("A post cannot contain both an image and a document.")

        payload = {
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
                media["altText"] = image_alt[:300]
            payload["content"] = {"media": media}

        if document_urn:
            payload["content"] = {"media": {"id": document_urn, "title": (document_title or "LinkedIn document")[:200]}}

        response = requests.post(f"{API_BASE}/posts", headers=self.headers, json=payload, timeout=self.timeout)
        self._raise(response, "post creation")
        return response.headers.get("x-restli-id") or response.headers.get("X-RestLi-Id") or "published-without-returned-id"
