def country(request):
    return {
        "current_country": getattr(request, "country", None),
    }
