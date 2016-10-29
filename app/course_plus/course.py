#coding=utf-8
from flask import Flask, jsonify, abort, g, make_response, request , url_for
from flask.ext.restful import Api, Resource
from flask.ext.httpauth import HTTPBasicAuth
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey
from app import app,db,api,getUrlOfKey,auth
import json
import datetime
from simple_result import SimpleResult


class Author(db.Model):
    __tablename__ = 't_author'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True)
    icon = db.Column(db.String(255))
    avatar = db.Column(db.String(255))
    phone = db.Column(db.String(16))
    email = db.Column(db.String(64))
    qq = db.Column(db.String(16))
    wechat = db.Column(db.String(32))
    introduction = db.Column(db.Text)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    contactCost = db.Column(db.Integer)
    topics = relationship("Topic", backref = "Author")

    def courses(self):
        topics = Topic.query.filter(Topic.authorId == self.id);
        course_ids = []
        for topic in topics:
            if topic.courseId not in course_ids:
                course_ids.append(topic.courseId)
        courses = []
        for courseId in course_ids:
            course = Course.query.get(courseId)
            courses.append(course.briefJson())
        return courses


    def actualIcon(self):
        return getUrlOfKey(self.icon)
    
    def actualAvatar(self):
        return getUrlOfKey(self.avatar)

    def simpleJson(self):
        return {"name":self.name,"icon":self.actualIcon(),"id":self.id}

    def json(self):
        resource = Resource.query.filter(Resource.authorId == self.id).first()
        attachmentId = None
        cost = 0
        if resource:
            attachmentId = resource.id
            cost = resource.cost
        return {"name":self.name,"avatar":self.actualAvatar(),"id":self.id,"description":self.introduction,"attachmentId":attachmentId,"resourceCost":cost,"contactCost":self.contactCost,"courses":self.courses()}

    

class School(db.Model):
    __tablename__ = 't_school'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    specialities = relationship("Speciality", backref = "School")

class Speciality(db.Model):
    __tablename__ = 't_speciality'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    schoolId = db.Column(db.Integer, ForeignKey('t_school.id'))
    courses = relationship("Course", backref = "Speciality")
    def json(self):
        return {"name":self.name, "id":self.id}


class Course(db.Model):
    __tablename__ = 't_course'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16))
    introduction = db.Column(db.Text)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    cover = db.Column(db.String(255))
    specialityId = db.Column(db.Integer, ForeignKey('t_speciality.id'))
    topics = relationship("Topic", backref = "Course")
    resources = relationship("Resource", backref = "Course")

    def topicNum(self):
        count = Topic.query.filter(Topic.courseId == self.id).count()
        return count

    def topics(self):
        topics = Topic.query.filter(Topic.courseId == self.id)
        topicsDic = {}
        for topic in topics:
            authorId = topic.authorId
            if (topicsDic.has_key(authorId)):
                topicsDic[authorId].append(topic.json())
            else:
                topicsDic[authorId] = [topic.json()]
        return topicsDic

    def actualCover(self):
        return getUrlOfKey(self.cover)

    def resourceNum(self):
        count = Resource.query.filter(Resource.courseId == self.id).count()
        return count

    def resources(self):
        resourcesJson = []
        resources = Resource.query.filter(Resource.courseId == self.id)
        for resource in resources:
            resourcesJson.append(resource.json())
        return resourcesJson


    def schoolName(self):
        speciality = Speciality.query.get(self.specialityId)
        school = School.query.get(speciality.schoolId)
        return school.name

    def specialityName(self):
        speciality = Speciality.query.get(self.specialityId)
        if speciality:
            return speciality.name
        return ""
    
    def authors(self):
        topics = Topic.query.filter(Topic.courseId == self.id)
        author_ids = []
        for topic in topics:
            if topic.authorId not in author_ids :
                author_ids.append(topic.authorId)
        authors = []
        for authorId in author_ids:
            author = Author.query.get(authorId)
            authors.append(author.simpleJson())
        return authors
    
    def detail_authors(self):
        topics = Topic.query.filter(Topic.courseId == self.id)
        author_ids = []
        for topic in topics:
            if topic.authorId not in author_ids :
                author_ids.append(topic.authorId)
        authors = []
        for authorId in author_ids:
            author = Author.query.get(authorId)
            authors.append(author.json())
        return authors

    def json(self):
        return {"id":self.id,
        "name":self.name,
        "topicNum":self.topicNum(),
        "resourceNum":self.resourceNum(),
        "schoolName":self.schoolName(),
        "specialityName":self.specialityName(),
        "specialityId":self.specialityId,
         "description":self.introduction,
        "resources":self.resources(),
        "topics":self.topics(),
        "authors":self.detail_authors(),
        "cover":self.actualCover()
        }

    def simpleJson(self):
        return {"id":self.id,
        "name":self.name,
        "topicNum":self.topicNum(),
        "resourceNum":self.resourceNum(),
        "schoolName":self.schoolName(),
        "specialityName":self.specialityName(),
        "specialityId":self.specialityId,
        "authors":self.authors(),
        "cover":self.actualCover()
        }
    
    def briefJson(self):
        return {"id":self.id,
        "name":self.name}


class Topic(db.Model):
    __tablename__ = 't_topic'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16))
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    courseId = db.Column(db.Integer, ForeignKey('t_course.id'))
    authorId = db.Column(db.Integer, ForeignKey('t_author.id'))
    bodys = relationship("TopicBody", backref = "Topic")
    comments = relationship("Comment", backref = "Topic")

    def json(self):
        return {"name":self.name,"authorId":self.authorId,"id":self.id}


class TopicBody(db.Model):
    __tablename__ = 't_topic_body'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer)
    content = db.Column(db.Text)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    topicId = db.Column(db.Integer, ForeignKey('t_topic.id'))

    def json(self):
        return {"id":self.id,"type":self.type,"content":self.content}




class TradeRecord(db.Model):
    __tablename__ = 't_trade'
    id = db.Column(db.Integer, primary_key=True)
    orderNo = db.Column(db.String(32))
    orderStatus = db.Column(db.Integer)  #0未支付 1已支付
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    cost = db.Column(db.Integer)
    attachmentId = db.Column(db.Integer, ForeignKey('t_attachment.id'))
    topicId = db.Column(db.Integer, ForeignKey('t_topic.id'))
    userId = db.Column(db.Integer, ForeignKey('t_user.id'))
    
    def json(self):    
        attachmentUrl = ""
        if self.attachmentId:
            attachment = Resource.query.get(self.attachmentId)
            attachmentUrl = getUrlOfKey(attachment.key)
        topic = Topic.query.get(self.topicId)
        return {"id":self.id,"topicId":self.topicId,"courseId":topic.courseId,"attachmentUrl":attachmentUrl,"authorId":topic.authorId,"attachmentId":self.attachmentId}
    

class Resource(db.Model):
    __tablename__ = 't_attachment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    key = db.Column(db.String(255))
    ext = db.Column(db.String(16))
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    cost = db.Column(db.Integer)
    authorId = db.Column(db.Integer, ForeignKey('t_author.id'))
    courseId = db.Column(db.Integer, ForeignKey('t_course.id'))

    def json(self):
        return {"id":self.id,"cost":self.cost,"resourceKey":self.key,"name":self.name,"ext":self.ext}


class Question(db.Model):
    __tablename__ = 't_question'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    replyContent = db.Column(db.Text)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    userEmail = db.Column(db.String(255))
    userId = db.Column(db.Integer, ForeignKey('t_user.id'))
    topicId = db.Column(db.Integer, ForeignKey('t_topic.id'))
    authorId = db.Column(db.Integer, ForeignKey('t_author.id'))


@app.route('/api/user/author/publishQuestion', methods=['POST'])
@auth.login_required
def publishQuestion():
    content = request.json.get("content")
    userEmail = request.json.get("email")
    userId = g.user.id
    topicId = request.json.get("topicId")
    authorId = request.json.get("authorId")
    if not authorId or not content or not userEmail or not topicId: 
        abort(400)
    trade = TradeRecord.query.filter(TradeRecord.authorId == authorId,TradeRecord.userId == g.user.id, TradeRecord.deletedAt == None).first()
    if trade:
        trade.deletedAt = datetime.datetime.now()
        db.session.add(trade)
        question = Question()
        question.content = content
        question.userEmail = userEmail
        question.userId = userId
        question.authorId = authorId
        question.topicId = topicId
        db.session.add(question)
        db.session.commit()
        return (jsonify(SimpleResult(0,"提问成功").json()),200)    
    return (jsonify(SimpleResult(-1,"没有提问权限").json()),400)

@app.route('/api/user/author/getQuestionChance', methods=['GET'])
@auth.login_required
def getQuestionChance():
    authorId = request.args.get("authorId")
    if not authorId:
        abort(400)
    trade = TradeRecord.query.filter(TradeRecord.authorId == authorId,TradeRecord.userId == g.user.id, TradeRecord.deletedAt == None).first()
    if trade:
        return (jsonify(trade.json()),200)    
    return (jsonify(SimpleResult(-1,"没有提问权限").json()),400)



@app.route('/api/user/resource/getDownloadUrl', methods=['GET'])
@auth.login_required
def getKeyUrl():
    id = request.args.get("id")
    if not id:
        abort(400)
    attachment = Resource.query.get(id)
    key = attachment.key
    if attachment.cost == 0:
        return (jsonify(SimpleResult(0,getUrlOfKey(key)).json()),200)
    trade = db.session.query(TradeRecord).filter(TradeRecord.attachmentId == id, TradeRecord.userId == g.user.id).first()
    if not trade:
        return (jsonify(SimpleResult(-1,"该资料并未被购买").json()),400)
    return (jsonify(SimpleResult(0,getUrlOfKey(key)).json()),200)

    

@app.route('/api/web/course/speciality', methods=['GET'])
def getSpecialList():
    schools = db.session.query(School).all()
    specialDic = {}
    for school in schools:
        schoolDic = {"id":school.id}
        specialityJsonList = []
        specialityList = Speciality.query.filter_by(schoolId = school.id)
        for speciality in specialityList:
            specialityJsonList.append(speciality.json())
        schoolDic["specialities"] = specialityJsonList
        specialDic[school.name] = schoolDic
    return (jsonify(specialDic),200)

@app.route('/api/web/course/courseList', methods=['GET'])
def getCourseList():
    page = request.args.get("page")
    limit = request.args.get("limit")
    key = request.args.get("key")
    speciality_id = request.args.get("specialityId")
    if not page or not limit:
        abort(400)
    if not speciality_id and not key:
        abort(400)
    courses = []
    page = int(page)
    limit = int(limit)
    if key:
        courses = db.session.query(Course).filter(Course.name.like("%"+key+"%")).limit(limit).offset(limit * (page-1))
    else:
        courses = db.session.query(Course).filter(Course.specialityId == speciality_id).limit(limit).offset(limit * (page-1))
    courseJsonList = []
    for course in courses:
        courseJsonList.append(course.simpleJson())
    print(courseJsonList)
    return (json.dumps(courseJsonList),200)


@app.route('/api/web/course/courseDetail', methods=['GET'])
def getCourseDetail():
    course_id = request.args.get("id")
    if not course_id:
        abort(400)
    course = Course.query.get(course_id)
    if not course:
        return (jsonify(SimpleResult(-1,"课程不存在").json()),400)
    else:
        return (jsonify(course.json()),200)
    

@app.route('/api/web/course/topicDetail', methods=['GET'])
def getTopicBody():
    topic_id = request.args.get("id")
    if not topic_id:
        abort(400)
    topic_body = TopicBody.query.filter(TopicBody.topicId == topic_id).first()
    if not topic_body:
        return (jsonify(SimpleResult(-1,"知识点不存在").json()),400)
    else:
        return (jsonify(topic_body.json()),200)



@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify(SimpleResult(-1,"缺少参数").json()), 400)

