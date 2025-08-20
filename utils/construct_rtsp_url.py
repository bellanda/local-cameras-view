"""
Utility functions for constructing RTSP URLs for different camera brands.
"""


def construct_rtsp_url(
    brand: str, username: str, password: str, ip: str, port: int = 554, channel: int = 1, stream_type: str = "main"
) -> str:
    """
    Construct RTSP URL based on camera brand and connection parameters.

    Args:
        brand: Camera brand (HIKVISION, EZVIZ, INTELBRAS, WEBCAM)
        username: Username for camera authentication
        password: Password for camera authentication
        ip: Camera IP address
        port: RTSP port (default: 554)
        channel: Camera channel number (default: 1)
        stream_type: Stream type - "main" or "sub" (default: "main")

    Returns:
        Constructed RTSP URL string

    Raises:
        ValueError: If brand is not supported
    """
    brand_upper = brand.upper()

    if brand_upper in ["HIKVISION", "EZVIZ"]:
        # HIKVISION and EZVIZ use the same URL format
        return f"rtsp://{username}:{password}@{ip}:{port}/Streaming/Channels/10{channel}"

    elif brand_upper == "INTELBRAS":
        # Intelbras standard format from rtsp.txt
        subtype = 0 if stream_type == "main" else 1
        return f"rtsp://{username}:{password}@{ip}:{port}/cam/realmonitor?channel={channel}&subtype={subtype}"

    elif brand_upper == "WEBCAM":
        # For webcams, return 0 to use with OpenCV
        return "0"

    else:
        raise ValueError(f"Unsupported camera brand: {brand}. Supported brands: HIKVISION, EZVIZ, INTELBRAS, WEBCAM")


def get_supported_brands() -> list[str]:
    """
    Get list of supported camera brands.

    Returns:
        List of supported brand names
    """
    return ["HIKVISION", "EZVIZ", "INTELBRAS", "WEBCAM"]


def is_webcam(brand: str) -> bool:
    """
    Check if the brand is a webcam (returns 0 for OpenCV).

    Args:
        brand: Camera brand name

    Returns:
        True if brand is WEBCAM, False otherwise
    """
    return brand.upper() == "WEBCAM"
