from django.db import models
from django.core.validators import MinValueValidator


class MSMEStatistic(models.Model):
    state = models.CharField(max_length=100, help_text="State / Union Territory or Region")
    sector = models.CharField(max_length=100, help_text="Industry sector (e.g. Manufacturing, Services, IT, Agriculture)")
    registered_units = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of registered MSME units"
    )
    year = models.PositiveIntegerField(help_text="Fiscal or calendar year (e.g. 2025, 2026)")
    notes = models.TextField(blank=True, default='', help_text="Reference data notes or source citation")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', 'state', 'sector']
        verbose_name = 'MSME Statistic'
        verbose_name_plural = 'MSME Statistics'

    def __str__(self):
        return f"{self.state} - {self.sector} ({self.year}): {self.registered_units:,} units"
