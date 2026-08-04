from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.assessments.models import Assessment
from apps.insights import services
from apps.journal.models import Entry


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
