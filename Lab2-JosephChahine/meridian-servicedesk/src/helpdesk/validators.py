# validators.py
#
# validators for file uploads, etc.

from django.utils.translation import gettext as _

from helpdesk import settings as helpdesk_settings

# TODO: can we use the builtin Django validator instead?
# see:
# https://docs.djangoproject.com/en/4.0/ref/validators/#fileextensionvalidator


def validate_file_extension(value):
    import os

    from django.core.exceptions import ValidationError

    name = value.name
    ext = os.path.splitext(name)[1]  # [0] returns path+filename
    # TODO: we might improve this with more thorough checks of file types
    # rather than just the extensions.

    if not helpdesk_settings.HELPDESK_VALIDATE_ATTACHMENT_TYPES:
        return

    # Reject double extensions outright (e.g. shell.php.png), since
    # os.path.splitext only looks at the last dot and would wrongly
    # treat this as a safe .png.
    if name.count(".") > 1:
        raise ValidationError(_("Filenames with more than one dot are not allowed."))

    # TODO: one more check in case it is a file with no extension; we
    # should always allow that?
    if ext.lower() not in helpdesk_settings.HELPDESK_VALID_EXTENSIONS and not (
        ext.lower() == "" or ext.lower() == "."
    ):
        raise ValidationError(_("Unsupported file extension: ") + ext.lower())

def reencode_image_if_needed(django_file):
    """For an image upload, decode it and save it back out, so only real
    pixel data survives; anything else those bytes might carry, like an
    embedded script, never makes it into the re-saved file.
    """
    import os
    from io import BytesIO

    from django.core.exceptions import ValidationError
    from django.core.files.uploadedfile import InMemoryUploadedFile

    ext = os.path.splitext(django_file.name)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        return django_file

    from PIL import Image

    # Cap the decoded dimensions before we load the pixels
    MAX_IMAGE_PIXELS = 25_000_000  # 25 megapixels, e.g. ~5000x5000

    django_file.seek(0)
    try:
        image = Image.open(django_file)
        image.verify()
        django_file.seek(0)
        image = Image.open(django_file)
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise ValidationError(_("Image dimensions are too large."))
        image.load()
    except ValidationError:
        raise
    except Exception:
        raise ValidationError(_("File does not appear to be a valid image."))

    buffer = BytesIO()
    fmt = "JPEG" if ext in (".jpg", ".jpeg") else "PNG"
    if fmt == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffer, format=fmt)
    buffer.seek(0)

    # Stamp the real, re-encoded format as the content type (not the client's
    # claim), so the stored record and the logs show the detected type.
    real_content_type = "image/jpeg" if fmt == "JPEG" else "image/png"
    return InMemoryUploadedFile(
        buffer, None, django_file.name, real_content_type,
        buffer.getbuffer().nbytes, None,
    )