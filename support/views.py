from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, reverse
from support.models import *
from django.contrib.auth.decorators import login_required
from support import forms
from accounts import subscribe


@login_required(login_url='main_page')
def support_main_page(request):
    template = 'support/main_page.html'
    context = {}
    MyTicket = Ticket.objects.filter(user = request.user)
    context['tickets'] = MyTicket
    if request.method == 'POST':
        data = request.POST
        ticket_sub = data.get('subject')
        ticket_msg = data.get('message')
        if ticket_msg and ticket_sub:
            new_ticket = Ticket.objects.create(
                title = ticket_sub,
                user = request.user,
            )
            new_msg = TicketMessage.objects.create(
                ticket = new_ticket,
                message = ticket_msg,
            )

    return render(request, template, context)


def all_ticket(request):
    type_tickets = request.GET.get('type', 'new')
    template = 'support/all_tickets.html'
    context = {}
    tickets = Ticket.objects.filter(status=type_tickets)
    context['tickets'] = tickets
    return render(request, template, context)

def answer_ticket_support(request, pk):
    template = 'support/answer_ticket.html'
    ticket = get_object_or_404(Ticket, pk = pk)
    context = {}
    context['form'] = forms.SupportAnswer()
    context['ticket_status'] = forms.TicketStatus(instance=ticket)
    context['messages'] = ticket.ticketmessage_set.all()
    if request.method == 'POST':
        form_answer = forms.SupportAnswer(request.POST)
        form_status = forms.TicketStatus(request.POST, instance=ticket)
        if form_answer.is_valid() and form_status.is_valid():
            message = form_answer.cleaned_data['message']
            form_answer = form_answer.save(commit=False)
            form_answer.ticket = ticket
            form_answer.support_user = request.user
            form_answer.save()
            form_status.save()
            subscribe.subscribe_answer_support(ticket.user.pk, message)
        return HttpResponseRedirect(request.path)
    return render(request, template, context)


def answer_ticket(request, pk):
    template = 'support/answer_ticket.html'
    ticket = get_object_or_404(Ticket, pk = pk)
    context = {}
    context['form'] = forms.SupportAnswer()
    context['messages'] = ticket.ticketmessage_set.all()
    if request.method == 'POST':
        data = request.POST
        msg_answer = data.get('answer')
        if msg_answer:
            ticket.status = 'open'
            ticket.save()
            TicketMessage.objects.create(
                ticket = ticket,
                message = msg_answer,
            )
            print(msg_answer)
            return HttpResponseRedirect(request.path)
    return render(request, template, context)