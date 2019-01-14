from django.shortcuts import render,redirect,get_object_or_404,get_list_or_404,render_to_response
from django.contrib.auth.models import User
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from .forms import QuizForm
from .models import Quiz, Question, Answers,Score
import os, csv
from random import shuffle
from django.core.mail import send_mail
from django.http import HttpResponse
from datetime import datetime, date
from django.utils.timezone import datetime, timedelta
def search(request):
    print('inside search')
    try:
        q = request.GET['search']
        print(q)
        quiz_byname= Quiz.objects.filter(name__icontains=q)
        quiz_bytag =Quiz.objects.filter(tags__icontains=q)
        quiz=[]
        for list in quiz_byname:
            quiz.append(list)
        for list in quiz_bytag:
            quiz.append(list)
        # print(quiz_bytag)
        return render(request,'dashboard.html', {'quiz_object':quiz})
    except:
        messages.error(request, 'Quiz does not exists!')
        return render(request,'dashboard.html')

def timer(request):
    return render(request,'indexTimer.html')
def home(request):
    if request.user.is_authenticated:
        return redirect('accounts/dashboard')
    else:
        return render(request, 'home.html')

@login_required(login_url = '/accounts/login')
def start(request):
    return render(request, 'instructions.html')


def start_quiz(request):

    if request.method == 'POST':
        try:
           item=Quiz.objects.get(Quiz_id=request.POST['quizid'])
           user = request.user
           instruct = item.instructions
           instruct_list = instruct.split(";")
           today =datetime.combine(date.min,datetime.now().time())+timedelta(hours=5,minutes=30)
           k = datetime.combine(date.min,item.start_time.time())
           if(today>k):
               # temp = datetime.combine(date.min, today.time()) - datetime.combine(date.min,item.start_time.time())
               temp = today -k
               if (temp > timedelta(minutes=0) and temp < timedelta(minutes=6)):
                   print(temp)
                   margin = 1
               else:
                   margin =0
           else:
               margin =0




           return render(request, 'instructions.html', {'quiz_object': item, 'user': user ,'instruct_list' :instruct_list ,'today':today,'margin':margin})
           # item=Quiz(Quiz_id=request.POST['quizid'],Test_password=request.POST['tPass'])

           # if item.Test_Password==request.POST['password']:
           #   request.session['username'] = request.user.get_username()
           #   return redirect('test/'+str(item.Quiz_id))
           # else:
           #
           #  # return render(request, 'start', {'error': 'Invalid Credentials!'})
           #  messages.info(request,'Invalid Credentials')
           #  return redirect('dashboard')
        except Quiz.DoesNotExist:
            messages.info(request,'Quiz does not exists!')
            return redirect('dashboard')
        else:
            return render(request, 'start')
    else:
        return redirect('started/quizid')

def quiz_auth(request, quizid):
    item = Quiz.objects.get(Quiz_id=quizid)
    item.duration = item.duration
    users=item.users_appeared.filter(pk=request.user.pk)

    if users.exists():
        messages.info(request, 'You already appeared in this Quiz')
        return redirect('dashboard')
    else:    
        if item.Test_Password == request.POST['password']:
            request.session['username'] = quizid
            if request.user.profile.role == 'client':
               item.users_appeared.add(request.user)

            return redirect('test/'+ str(quizid))
        else:
    
            # return render(request, 'start', {'error': 'Invalid Credentials!'})
            messages.info(request, 'Invalid Credentials')
            return redirect('dashboard')

def clean(f):
    data = list()
    with open(f, 'r') as file:
        text = file.read()
    list1 = text.split('\n')
    list1 = list1[1:]
    for item in list1:
        list2 = item.split(',')
        data.append(list2)
    return data

@login_required(login_url = '/accounts/login')
def create(request):
    user = request.user
    if user.profile.role == 'admin':
        if request.method == 'POST':
            # form is submitted
            quiz_form = QuizForm(request.POST, request.FILES, request.user)
            if quiz_form.is_valid:
                item = Quiz()
                try:
                    qu = Quiz.objects.get(Quiz_id = request.POST['Quiz_id'])
                    create_quiz_form = QuizForm()
                    return render(request, 'create_quiz.html', {'quiz_form': create_quiz_form, 'error': "Quiz id is already taken! "})
                except Quiz.DoesNotExist:
                    item.name = request.POST['name']
                    item.csv_file = request.FILES['csv_file']
                    item.about = request.POST['about']
                    item.Quiz_id=request.POST['Quiz_id']
                    item.Test_Password=request.POST['Test_Password']
                    item.instructions = request.POST['instructions']
                    item.positive = request.POST['positive']
                    item.negative = request.POST['negative']
                    item.duration = request.POST['duration']
                    item.start_time = request.POST['start_time']
                    item.end_time = request.POST['end_time']
                    item.quizmaster = request.user
                    item.tags=request.POST['tags']
                    item.save()
                    url = item.csv_file.url
                    l = url.split('/')
                    s = "\\"
                    s = s.join(l)
                    f = os.getcwd() + url
                    data = clean(f)
                    for row in data:
                        ques = Question()
                        ques.quiz = item
                        ques.question = row[0]
                        ques.a = row[1]
                        ques.b = row[2]
                        ques.c = row[3]
                        ques.d = row[4]
                        ques.correct = row[5]
                        ques.save()

                    messages.info(request,'Your Quiz has been submitted successfully. Share the credentials and start   quizzing!')
                    return redirect('/quiz/test/edit/' + item.Quiz_id)
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            # get request. We have to return the form so that user can fill it.
            create_quiz_form = QuizForm()
            return render(request, 'create_quiz.html', {'quiz_form': create_quiz_form})
    else:
        messages.info(request, 'You do not have the permissions required create a quiz')
        return redirect('dashboard')

def create_answer_table(quiz_object, question_objects, user_object):
    for question_object in question_objects:
        ans = Answers()
        ans.applicant = user_object
        ans.quiz = quiz_object
        ans.question = question_object
        ans.correct_choice = question_object.correct
        ans.save()
    return

@login_required(login_url = '/accounts/login')
def score(request, quizid):
    del request.session['username']
    aspirant = request.user

    item = get_object_or_404(Quiz, Quiz_id=quizid)
    answers = Answers.objects.filter(quiz = item, applicant=aspirant)
    list_object = []
    marks = 0
    for answer in answers:
        dicty = dict()
        ques = answer.question
        dicty['question'] = ques.question
        dicty['submission'] = answer.response
        dicty['correct'] = answer.correct_choice
        if answer.response == '':
            marks = marks
            dicty['result'] = '0'
        else:
            if answer.response == answer.correct_choice:
                dicty['result'] = '+' + str(item.positive)
                marks = marks + item.positive
            else:
                dicty['result'] = '-' + str(item.negative)
                marks = marks - item.negative
        list_object.append(dicty)
        total_marks = (item.positive) * len(list_object)
    try:
        score_data = get_object_or_404(Score, applicant=aspirant, quiz=item)
    except:
        score_data = Score()
    score_data.applicant = aspirant
    score_data.quiz = item
    score_data.obtained = marks
    score_data.total = total_marks
    score_data.save()
    return render(request, 'score.html', {'quiz_object': item, 'score': marks, 'data': list_object, 'max': total_marks})

@login_required(login_url = '/accounts/login')
def conduct_quiz(request, quizid):
    if request.session['username']==quizid:
        aspirant = request.user
        item = get_object_or_404(Quiz, Quiz_id=quizid)
        data = Question.objects.filter(quiz = item)
        if request.method == 'POST':
            ques = Question.objects.get(id= request.POST.get('question_id'))
            answer_object = Answers.objects.get(applicant=aspirant, quiz=item, question=ques)
            answer_object.response = request.POST.get('response')
            answer_object.save()

        querys = []
        for thing in data:
            querys.append(thing)

        else:
            try:
                answers = get_list_or_404(Answers, applicant=aspirant, quiz=item)
            except:
                create_answer_table(item, data, aspirant)
                shuffle(querys)

        return render(request, 'Quiz1.html', {'quiz_object': item, 'quiz_data': querys, 'user':aspirant})

@login_required(login_url = '/accounts/login')
def edit_quiz(request, quizid):
    aspirant = request.user
    if aspirant.profile.role == 'admin':
        item = get_object_or_404(Quiz, Quiz_id=quizid)
        data = Question.objects.filter(quiz = item)
        if request.method == 'POST':
            if aspirant == item.quizmaster:
                ques = get_object_or_404(Question, id=request.POST.get('question_id'))
                ques.image = request.POST.get('img')
                ques.code = request.POST.get('code')
                ques.save()
            else:
                error = 'You do not have the required Permissions.'
        querys = []
        for thing in data:
            querys.append(thing)
        # if error:
        #    print(error)
        return render(request, 'editquiz.html', {'quiz_object': item, 'quiz_data': querys })
    else:
        messages.info(request, 'You do not have the permissions required to edit this quiz')
        return redirect('dashboard')

@login_required(login_url = '/accounts/login')
def quizadmin(request):
    user = request.user
    if user.profile.role == 'admin':
        quiz_objects = Quiz.objects.filter(quizmaster= user)
        scores = []
        for quiz_object in quiz_objects:
            quiz_score = Score.objects.filter(quiz=quiz_object).order_by('-obtained')
            print(quiz_score)
            scores.append(quiz_score)
        return render(request, 'quizadmin.html', {'user': user, 'quiz_objects': quiz_objects, 'scores': scores})
    else:
        messages.info(request, 'You do not have the permissions required to view the admin-panel')
        return redirect('dashboard')

def leaderboard(request, quizid):
    user = request.user
    if user.profile.role == 'admin':
        quiz_object = get_object_or_404(Quiz, Quiz_id = quizid)
        score = Score.objects.filter(quiz=quiz_object).order_by('-obtained')
        return render(request,'leaderboard.html', {'quiz_object': quiz_object, 'scores': score})
    else:
        messages.info(request, 'You do not have the permissions required to view the admin-panel')
        return redirect('dashboard')

def export(request, quizid):
    user = request.user
    quiz_object = get_object_or_404(Quiz, Quiz_id = quizid)
    if user == quiz_object.quizmaster:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="result.csv"'
        writer = csv.writer(response)
        writer.writerow(['username','First name','Last name','Email address','Marks Obtained','Maximum Marks'])
        scores = Score.objects.filter(quiz=quiz_object).order_by('-obtained')
        result = list()
        for score in scores:
            user = score.applicant
            username = user.username
            firstname = user.first_name
            last_name = user.last_name
            email = user.email
            obtnd = score.obtained
            total = score.total
            percentage = score.percentage
            tup = (username,firstname,last_name,email,obtnd,total)
            result.append(tup)
        for score in result:
            writer.writerow(score)
        return response
    else:
        return HttpResponse("You do not have the authorization")