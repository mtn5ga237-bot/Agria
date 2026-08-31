from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleRequisMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restreint l'acces a une vue aux utilisateurs disposant de l'un des roles autorises.

    Utilise conjointement avec login_required (test T11 : redirection puis acces refuse
    a un compte agriculteur tentant d'acceder a une page reservee).
    """

    roles_autorises = ()

    def test_func(self):
        return self.request.user.a_le_role(*self.roles_autorises)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("Votre role ne vous permet pas d'acceder a cette page.")


class AgentOuPlusMixin(RoleRequisMixin):
    roles_autorises = ('agent', 'expert', 'admin')


class AgentRequisMixin(RoleRequisMixin):
    """Reserve aux agents vulgarisateurs (gestion de leur portefeuille de producteurs)."""

    roles_autorises = ('agent',)


class ExpertRequisMixin(RoleRequisMixin):
    roles_autorises = ('expert', 'admin')


class AdministrateurRequisMixin(RoleRequisMixin):
    roles_autorises = ('admin',)
