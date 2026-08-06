import csv
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.assessments.models import Assessment, ItemResponse
from apps.esm.models import Ping, PingResponse
from apps.goals.models import Goal
from apps.goals.services import orphan_sessions
from apps.insights import services
from apps.insights.forms import WeeklyReviewForm
from apps.insights.models import WeeklyReview
from apps.journal.models import Entry
from apps.library.models import BookCard
from apps.sessions_log.models import Session


@login_required
def dashboard(request):
    series = services.weekly_dp_flow_series(num_weeks=2)
    this_week, last_week = series[-1], series[-2]
    latest_setback = Entry.objects.filter(kind=Entry.SETBACK).order_by("-created_at").first()

    context = {
        "this_week": this_week,
        "last_week": last_week,
        "streaks": services.streaks(),
        "latest_setback": latest_setback,
        "flow_map": services.flow_map_points(window_days=14),
    }
    return render(request, "insights/dashboard.html", context)


@login_required
def insights(request):
    series = services.weekly_dp_flow_series(num_weeks=12)
    context = {
        "flow_map": services.flow_map_points(),
        "activity_ranking": services.flow_activity_ranking(),
        "weekly_series": series,
        "correlation": services.dp_flow_correlation(series),
        "streaks": services.streaks(),
        "active_day_percentage": services.active_day_percentage(),
        "heatmap": services.weekly_minutes_by_mid_goal(num_weeks=12),
        "mindset_ratio": services.monthly_mindset_ratio(),
        "dp_quality": services.dp_quality(),
        "grit_history": services.assessment_history(kind=Assessment.GRIT),
        "mindset_history": services.assessment_history(kind=Assessment.MINDSET),
    }
    return render(request, "insights/insights.html", context)


@login_required
def review(request):
    # The most recently *completed* week — series[-1] is the current, in-progress week.
    series = services.weekly_dp_flow_series(num_weeks=3)
    last_week, week_before = series[-2], series[-3]
    week_start = last_week["week_start"]
    week_end = week_start + timedelta(days=6)

    flow_delta = None
    if last_week["flow_rate"] is not None and week_before["flow_rate"] is not None:
        flow_delta = last_week["flow_rate"] - week_before["flow_rate"]

    review_obj, _ = WeeklyReview.objects.get_or_create(week_start=week_start)

    if request.method == "POST":
        form = WeeklyReviewForm(request.POST, instance=review_obj)
        if form.is_valid():
            form.save()
            return redirect(reverse("review"))
    else:
        form = WeeklyReviewForm(instance=review_obj)

    context = {
        "week_start": week_start,
        "week_end": week_end,
        "last_week": last_week,
        "flow_delta": flow_delta,
        "setbacks": Entry.objects.filter(
            kind=Entry.SETBACK, created_at__date__gte=week_start, created_at__date__lte=week_end
        ),
        "orphans": orphan_sessions(),
        "form": form,
    }
    return render(request, "insights/review.html", context)


_EXPORTABLE = {
    "goals": Goal,
    "sessions": Session,
    "journal": Entry,
    "esm_pings": Ping,
    "esm_responses": PingResponse,
    "assessments": Assessment,
    "assessment_items": ItemResponse,
    "library": BookCard,
    "weekly_reviews": WeeklyReview,
}


@login_required
def export_index(request):
    return render(request, "insights/export.html", {"models": sorted(_EXPORTABLE)})


@login_required
def export_csv(request, model_name):
    model = _EXPORTABLE.get(model_name)
    if model is None:
        return HttpResponse("Unknown export.", status=404)

    fields = [f.name for f in model._meta.concrete_fields]
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{model_name}.csv"'
    writer = csv.writer(response)
    writer.writerow(fields)
    for obj in model.objects.all().order_by("pk"):
        writer.writerow([getattr(obj, f) for f in fields])
    return response
