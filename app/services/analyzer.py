from app.utils.mongo import db
from fastapi import HTTPException
from app.models.analyzer import AddCandidate, AddAnalyzedData
from bson import ObjectId
from bson import ObjectId

class AnalyzerService:

    async def add_candidate_info(self, candidate: dict) -> bool:        
        try:
            candidate_data = AddCandidate(**candidate).dict()
            candidate_data['user_id'] = ObjectId(candidate_data['user_id'])
            result = await db.candidate.insert_one(candidate_data)
            return str(result.inserted_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def add_analyzed_data(self, analyzed_data: dict) -> bool:
        try:
            analyzed_data = AddAnalyzedData(**analyzed_data).dict()
            analyzed_data['candidate_id'] = ObjectId(analyzed_data['candidate_id'])
            analyzed_data['user_id'] = ObjectId(analyzed_data['user_id'])
            await db.analyzed_data.insert_one(analyzed_data)
            return True

        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def store_analyzed_data_with_candidate_id(self, candidate_id: str, technical_data: dict, communication_data: dict = None) -> bool:
        """
        Stores analyzed data for a candidate by candidate_id.
        If a document with the candidate_id exists, update it; otherwise, insert a new one.
        """
        try:
            query = {'candidate_id': ObjectId(candidate_id)}
            update_doc = {
                '$set': {
                    'technical_data': technical_data
                }
            }
            if communication_data is not None:
                update_doc['$set']['communication_data'] = communication_data

            result = await db.analyzed_data.update_one(
                query,
                update_doc,
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Failed to store analyzed data for candidate {candidate_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")



    # async def get_all_assessments(self) -> list:
    #     """
    #     Retrieve all assessments with proper aggregation and projection.
    #     Returns a list of assessment documents.
    #     """
    #     try:
    #         pipeline = [
    #             {"$match": {"is_deleted": False}},
    #             {"$sort": {"created_at": -1}},
    #             {
    #                 "$lookup": {
    #                     "from": "analyzed_data",
    #                     "localField": "_id",
    #                     "foreignField": "candidate_id",
    #                     "as": "result"
    #                 }
    #             },
    #             {"$unwind": {"path": "$result"}},
    #             {
    #                 "$project": {
    #                     "_id": 0,
    #                     "updated_at": 0,
    #                     "is_deleted": 0,
    #                     "result._id": 0,
    #                     "result.candidate_id": 0,
    #                     "result.created_at": 0,
    #                     "result.updated_at": 0,
    #                     "result.is_deleted": 0
    #                 }
    #             }
    #         ]
    #         cursor = db.candidate.aggregate(pipeline)
    #         results = []
    #         async for doc in cursor:
    #             # Extract required fields from the nested structure
    #             result = doc.get("result", {})
    #             communication_data = result.get("communication_data", {})
    #             key_metrics = communication_data.get("key_metrics", {})
    #             # Get date only (remove time if present)
    #             created_at = doc.get("created_at", "")
    #             date_only = created_at.date().isoformat()
            

    #             assessment = {
    #                 "candidate_name": doc.get("candidate_name"),
    #                 "email": doc.get("email"),
    #                 "phone": doc.get("phone"),
    #                 "communication_score": communication_data.get("communication_score"),
    #                 "resume_score": result.get("analyze_answer_response", {}).get("match_score"),
    #                 "overall_score": result.get("technical_data", {}).get("overall_score"),
    #                 "technical_score": result.get("technical_data", {}).get("technical_score"),
    #                 "status": result.get("technical_data", {}).get("fit"),
    #                 "date": date_only
    #             }
    #             results.append(assessment)
    #         return results
    #     except Exception as e:
    #         print("Error in aggregation:", e)
    #         return []


    async def get_all_assessments(self, skip: int, limit: int, search: str,user_id: str) -> list:
        """
        Retrieve paginated assessments with proper aggregation and projection.
        
        :param skip: Number of documents to skip
        :param limit: Number of documents to return
        :return: Tuple (list of assessments, total count of assessments)
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)     
            
            print("user_id",user_id)
            print("Type os user_id",type(user_id))
            print("Search ",search) 

            match_filter = {"is_deleted": False, "user_id": user_id}

            if search and search.strip():
                match_filter["$or"] = [
                    {"job_position": {"$regex": search, "$options": "i"}},
                    {"hr_name": {"$regex": search, "$options": "i"}},
                    {"candidate_name": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}}
                ]

            pipeline = [
                {"$match": match_filter},
                {"$sort": {"created_at": -1}},
                {
                    "$lookup": {
                        "from": "analyzed_data",
                        "localField": "_id",
                        "foreignField": "candidate_id",
                        "as": "result"
                    }
                },
                {"$unwind": {"path": "$result"}},
                {
                    "$project": {
                        "_id": 0,
                        "updated_at": 0,
                        "is_deleted": 0,
                        "result._id": 0,
                        "result.candidate_id": 0,
                        "result.created_at": 0,
                        "result.updated_at": 0,
                        "result.is_deleted": 0
                    }
                },
                {"$skip": skip},
                {"$limit": limit}
            ]

            cursor = db.candidate.aggregate(pipeline)
            results = []

            async for doc in cursor:
                result = doc.get("result", {})
                communication_data = result.get("communication_data", {})
                
                created_at = doc.get("created_at")
                date_only = created_at.date().isoformat() if created_at else None

                assessment = {
                    "candidate_name": doc.get("candidate_name"),
                    "email": doc.get("email"),
                    "phone": doc.get("phone"),
                    "hr_name": doc.get("hr_name"),
                    "job_position": doc.get("job_position"),
                    "communication_score": communication_data.get("communication_score"),
                    "resume_score": result.get("analyze_answer_response", {}).get("match_score"),
                    "overall_score": result.get("technical_data", {}).get("overall_score"),
                    "technical_score": result.get("technical_data", {}).get("technical_score"),
                    "status": result.get("technical_data", {}).get("fit"),
                    "date": date_only
                }
                results.append(assessment)

            # Get total count for pagination
            total_count = await db.candidate.count_documents({"is_deleted": False})

            return results, total_count

        except Exception as e:
            print("Error in aggregation:", e)
            return [], 0


    async def add_communication_data(self, candidate_id: str, communication_data: dict) -> bool:
        try:
            result = await db.analyzed_data.update_one(
                {"candidate_id": ObjectId(candidate_id), "communication_data": {"$exists": False}},  
                {"$set": {"communication_data": communication_data}}
            )

            if result.modified_count == 0:
                print("Failed to add communication data")
                return False  

            print("Communication data added successfully")
            return True  

        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def get_candidate_by_email(self, email: str) -> dict:
        try:
            candidate = await db.candidate.find_one({"email": email, "is_deleted": False})
            if not candidate:
                return None
            return candidate
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal Server Error")
        
    async def store_quiz_questions(self, candidate_uid: str, quiz_data: list) -> bool:
        try:
            res = await db.analyzed_data.update_one(
                {"candidate_id": ObjectId(candidate_uid)},  # use correct field
                {"$push": {"quiz_questions": {"$each": quiz_data}}},  # append instead of overwrite
                upsert=True  # create if it doesn't exist
            )
            if res:
                print("Quiz questions stored successfully")
                return True
            print("Failed to store quiz questions")
            return False
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    async def get_quiz_question_by_id(self, candidate_uid: str, quiz_id: str) -> dict:
        try:
            
            analyzed_data = await db.analyzed_data.find_one({"candidate_id": ObjectId(candidate_uid)})
            if analyzed_data and "quiz_questions" in analyzed_data:
                for question in analyzed_data["quiz_questions"]:
                    if str(question.get("quiz_id")) == str(quiz_id):
                        return question
            return {}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
        
    async def get_quiz_questions(self,candidate_id: str):
        try:

            result = await db.analyzed_data.find_one({"candidate_id": ObjectId(candidate_id)}, {"quiz_questions": 1, "_id": 0})
            if result:
                return result["quiz_questions"]
            else:
                return None
        except Exception as e:
            print("Error in get_quiz_questions:", e)
            return None

    async def save_score(self, candidate_id: str, quiz_id: str, score_type: str, score: float) -> bool:
        try:
            res = await db.analyzed_data.update_one(
                {
                    "candidate_id": ObjectId(candidate_id),
                    "quiz_questions.quiz_id": quiz_id
                },
                {
                    "$set": {
                        "quiz_questions.$.type": score_type,
                        "quiz_questions.$.score": score
                    }
                }
            )
            
            if res.matched_count > 0:
                print(f"Successfully updated quiz {quiz_id} for candidate {candidate_id}")
                print(f"Modified count: {res.modified_count}")
                return True
            else:
                print(f"No matching document found for candidate {candidate_id} with quiz {quiz_id}")
                return False
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
        
    async def get_score(self, candidate_id: str):
        try:
            result = await db.analyzed_data.find_one(
                {"candidate_id": ObjectId(candidate_id)},
                {"quiz_questions": 1, "_id": 0}  # Only return quiz_questions field
            )
            
            if result and "quiz_questions" in result:
                print(f"Found {len(result['quiz_questions'])} quiz questions for candidate {candidate_id}")
                return result["quiz_questions"]
            else:
                print(f"No quiz questions found for candidate {candidate_id}")
                return []
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
        
    async def get_candidate_analysis_by_id(self, candidate_id: str) -> dict:
        try:

            # Query the database
            candidate = await db.analyzed_data.find_one(
                {"candidate_id": ObjectId(candidate_id), "is_deleted": False},
                {"analyze_answer_response": 1, "communication_data": 1}  # Only return these fields
            )

            if not candidate:
                return None

            return candidate

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
        
    async def get_candidate_by_id(self, id: str) -> dict:
        try:
            candidate = await db.candidate.find_one({"_id": ObjectId(id), "is_deleted": False})
            candidate['_id'] = str(candidate['_id'])
            candidate['created_at'] = str(candidate['created_at'])
            candidate['updated_at'] = str(candidate['updated_at'])
            if not candidate:
                return None
            return candidate
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal Server Error")