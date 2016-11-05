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
from user import getCurrentUser

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

    def json(self,courseId,user):
        resource = Resource.query.filter(Resource.authorId == self.id).first()
        attachmentId = None
        cost = 0
        authorCourseId = None
        if resource:
            attachmentId = resource.id
            cost = resource.cost
        if courseId:
            authorCourse = AuthorCourse.query.filter(AuthorCourse.courseId == courseId, AuthorCourse.authorId == self.id).first()
            if authorCourse:
                authorCourseId = authorCourse.id
        if authorCourse is not None:
            #是否买断
            trade = None
            if user:
                print(user)
                trade = TradeRecord.query.filter(TradeRecord.authorCourseId == authorCourse.id, TradeRecord.userId == user.id, TradeRecord.orderStatus == 1, TradeRecord.type == 4).first()
            if not trade:
                return {"courseCost":authorCourse.cost,"authorCourseId":authorCourseId,"name":self.name,"avatar":self.actualAvatar(),"id":self.id,"description":self.introduction,"attachmentId":attachmentId,"resourceCost":cost,"contactCost":self.contactCost,"courses":self.courses()}
            return {"courseCost":authorCourse.cost,"qqGroupId":authorCourse.qqGroupId,"inviteCode":trade.orderNo,"authorCourseId":authorCourseId,"name":self.name,"avatar":self.actualAvatar(),"id":self.id,"description":self.introduction,"attachmentId":attachmentId,"resourceCost":cost,"contactCost":self.contactCost,"courses":self.courses()}
        else:
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
    
    def detail_authors(self,user):
        topics = Topic.query.filter(Topic.courseId == self.id)
        author_ids = []
        for topic in topics:
            if topic.authorId not in author_ids :
                author_ids.append(topic.authorId)
        authors = []
        for authorId in author_ids:
            author = Author.query.get(authorId)
            authors.append(author.json(self.id,user))
        return authors

    def json(self,user):
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
        "authors":self.detail_authors(user),
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
    weight = db.Column(db.Integer)
    cost = db.Column(db.Integer)
    qqGroupId = db.Column(db.String(16))
    type = db.Column(db.Integer)  #1 知识点 2课
    bodys = relationship("TopicBody", backref = "Topic")
    comments = relationship("Comment", backref = "Topic")

    def json(self):
        return {"name":self.name,"authorId":self.authorId,"id":self.id,"weight":self.weight,"qqGroupId":self.qqGroupId,"cost":self.cost}


class TopicBody(db.Model):
    __tablename__ = 't_topic_body'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer)
    content = db.Column(db.Text)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    topicId = db.Column(db.Integer, ForeignKey('t_topic.id'))
    def json(self,user):
        topic = Topic.query.get(self.topicId)
        if user is not None:
            if topic.type == 2: #是门课程
                # 需要先检查有没有被买断
                courseId = topic.courseId
                authorId = topic.authorId
                authorCourse = AuthorCourse.query.filter(AuthorCourse.courseId == courseId, AuthorCourse.authorId == authorId).first()
                trade = None
                # 如果存在这门课，检查有没有被买断
                if authorCourse:
                    trade = TradeRecord.query.filter(TradeRecord.authorCourseId == authorCourse.id, TradeRecord.userId == user.id, TradeRecord.orderStatus == 1, TradeRecord.type == 4).first()
                if trade:
                    return {"id":self.id,"type":topic.type,"content":self.content,"qqGroupId":authorCourse.qqGroupId,"inviteCode":trade.orderNo,"cost":topic.cost}
                else:
                    #检查有没有购买这节课时
                    trade = TradeRecord.query.filter(TradeRecord.topicId == self.topicId, TradeRecord.userId == user.id, TradeRecord.orderStatus == 1, TradeRecord.type == 3).first()
                    if trade:
                        return {"id":self.id,"type":topic.type,"content":self.content,"qqGroupId":topic.qqGroupId,"inviteCode":trade.orderNo,"cost":topic.cost}
                    else:
                        return {"id":self.id,"type":topic.type,"content":self.content,"cost":topic.cost}
            else:
                return {"id":self.id,"type":topic.type,"content":self.content,"cost":topic.cost}
        else:
            return {"id":self.id,"type":topic.type,"content":self.content,"cost":topic.cost}


    
class AuthorCourse(db.Model):
    __tablename__ = 't_author__course'
    id = db.Column(db.Integer, primary_key=True)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    qqGroupId = db.Column(db.String(16))
    cost = db.Column(db.Integer)
    courseId = db.Column(db.Integer, ForeignKey('t_course.id'))
    authorId = db.Column(db.Integer, ForeignKey('t_author.id'))


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
    authorCourseId = db.Column(db.Integer, ForeignKey('t_author__course.id'))
    type = db.Column(db.Integer)  # 资料下载  2 提问 3 课程购买 4 课时买断

    def json(self):    
        attachmentUrl = ""
        if self.attachmentId:
            attachment = Resource.query.get(self.attachmentId)
            attachmentUrl = getUrlOfKey(attachment.key)
        topic = Topic.query.get(self.topicId)
        #课程买断
        if self.type == 4:
            authorCourse = AuthorCourse.query.get(self.authorCourseId)
            return {"qqGroupId":authorCourse.qqGroupId,"inviteCode":self.orderNo,"type":self.type,"id":self.id,"authorCourseId":self.authorCourseId,"topicId":self.topicId,"courseId":topic.courseId,"attachmentUrl":attachmentUrl,"authorId":topic.authorId,"attachmentId":self.attachmentId}            
        #课时购买
        if self.type == 3:
            return {"qqGroupId":topic.qqGroupId,"inviteCode":self.orderNo,"type":self.type,"id":self.id,"authorCourseId":self.authorCourseId,"topicId":self.topicId,"courseId":topic.courseId,"attachmentUrl":attachmentUrl,"authorId":topic.authorId,"attachmentId":self.attachmentId}
        else:
            return {"type":self.type,"id":self.id,"authorCourseId":self.authorCourseId,"topicId":self.topicId,"courseId":topic.courseId,"attachmentUrl":attachmentUrl,"authorId":topic.authorId,"attachmentId":self.attachmentId}
      

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
    authorId = int(authorId)
    trade_list = TradeRecord.query.filter(TradeRecord.attachmentId == None, TradeRecord.userId == g.user.id, TradeRecord.orderStatus == 1, TradeRecord.deletedAt == None)
    targetTrade = None
    for trade in trade_list:
        topic = Topic.query.get(trade.topicId)
        if topic.authorId == authorId:
            targetTrade = trade 
            break
    if targetTrade:
        targetTrade.deletedAt = datetime.datetime.now()
        db.session.add(targetTrade)
        question = Question()
        question.content = content
        question.userEmail = userEmail
        question.userId = userId
        question.authorId = authorId
        question.topicId = topicId
        question.createdAt = datetime.datetime.now()
        question.updatedAt = question.createdAt
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
    authorId = int(authorId)
    trade_list = TradeRecord.query.filter(TradeRecord.attachmentId == None, TradeRecord.userId == g.user.id, TradeRecord.orderStatus == 1, TradeRecord.deletedAt == None)
    for trade in trade_list:
        topic = Topic.query.get(trade.topicId)
        if topic.authorId == authorId:
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
    trade = db.session.query(TradeRecord).filter(TradeRecord.attachmentId == id, TradeRecord.userId == g.user.id, TradeRecord.orderStatus == 1).first()
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
    return (json.dumps(courseJsonList),200)


@app.route('/api/web/course/courseDetail', methods=['GET'])
def getCourseDetail():
    user = getCurrentUser(request)
    course_id = request.args.get("id")
    if not course_id:
        abort(400)
    course = Course.query.get(course_id)
    if not course:
        return (jsonify(SimpleResult(-1,"课程不存在").json()),400)
    else:
        return (jsonify(course.json(user)),200)
    

@app.route('/api/web/course/topicDetail', methods=['GET'])
def getTopicBody():
    topic_id = request.args.get("id")
    user = getCurrentUser(request)
    if not topic_id:
        abort(400)
    topic_body = TopicBody.query.filter(TopicBody.topicId == topic_id).first()            
    if not topic_body:
        return (jsonify(SimpleResult(-1,"知识点不存在").json()),400)
    return (jsonify(topic_body.json(user)),200)



@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify(SimpleResult(-1,"缺少参数").json()), 400)

