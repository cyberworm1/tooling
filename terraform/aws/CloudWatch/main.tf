provider "aws" {
  region = "us-west-2"
}

resource "aws_cloudwatch_dashboard" "render_dashboard" {
  dashboard_name = "RenderQueueMonitoring"
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Batch", "JobQueueDepth", "JobQueueName", "render-queue"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-west-2"
          title   = "Render Queue Depth"
        }
      }
    ]
  })
}

resource "aws_cloudwatch_metric_alarm" "high_queue" {
  alarm_name          = "HighRenderQueueDepth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "JobQueueDepth"
  namespace           = "AWS/Batch"
  period              = 300
  statistic           = "Average"
  threshold           = 100  # Alert if >100 jobs pending
  alarm_actions       = [aws_sns_topic.alerts.arn]
  dimensions = {
    JobQueueName = "render-queue"
  }
}

resource "aws_sns_topic" "alerts" {
  name = "render-alerts"
}