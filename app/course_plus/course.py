#coding=utf-8
from flask import Flask, jsonify, abort, g, make_response, request , url_for
from flask.ext.restful import Api, Resource
from flask.ext.httpauth import HTTPBasicAuth
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey
from app import app,db,api
import json
import datetime
from simple_result import SimpleResult


class Author(db.Model):
    __tablename__ = 't_author'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True)
    icon = db.Column(db.String(16))
    avatar = db.Column(db.String(16))
    phone = db.Column(db.String(16))
    email = db.Column(db.String(64))
    qq = db.Column(db.String(16))
    wechat = db.Column(db.String(32))
    resourceKey = db.Column(db.String(16))
    introduction = db.Column(db.Text)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
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

    def simpleJson(self):
        return {"name":self.name,"icon":self.icon,"id":self.id}
    def json(self):
        return {"name":self.name,"avatar":self.avatar,"id":self.id,"description":self.introduction,"resourceKey":self.resourceKey,"courses":self.courses()}

    

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
    cover = db.Column(db.String(32))
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
        "authors":self.detail_authors()
        }

    def simpleJson(self):
        return {"id":self.id,
        "name":self.name,
        "topicNum":self.topicNum(),
        "resourceNum":self.resourceNum(),
        "schoolName":self.schoolName(),
        "specialityName":self.specialityName(),
        "specialityId":self.specialityId,
        "authors":self.authors()}
    
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


class Resource(db.Model):
    __tablename__ = 't_attachment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    key = db.Column(db.String(32))
    ext = db.Column(db.String(16))
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    courseId = db.Column(db.Integer, ForeignKey('t_course.id'))

    def json(self):
        return {"id":self.id,"key":self.key,"name":self.name,"ext":self.ext}


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
    limit = request.args.get("limit",20)
    key = request.args.get("key")
    if not page:
        abort(400)
    courses = []
    page = int(page)
    if key:
        courses = db.session.query(Course).filter(Course.name.like("%"+key+"%")).limit(limit).offset(limit * (page-1))
    else:
        courses = db.session.query(Course).limit(limit).offset(limit * (page-1))
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
        return (jsonify(SimpleResult(-1,"课程不存在").json()),200)
    else:
        return (jsonify(course.json()),200)
    

@app.route('/api/web/course/topicDetail', methods=['GET'])
def getTopicBody():
    topic_id = request.args.get("id")
    if not topic_id:
        abort(400)
    topic_body = TopicBody.query.filter(TopicBody.topicId == topic_id).first()
    if not topic_body:
        return (jsonify(SimpleResult(-1,"知识点不存在").json()),200)
    else:
        return (jsonify(topic_body.json()),200)



@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify(SimpleResult(-1,"缺少参数").json()), 400)

